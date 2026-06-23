"""
AI Traffic Inspector — API Routes
REST endpoints for the traffic violation detection system.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import (
    get_db, get_violations, get_violation_by_id, delete_violation,
    get_analytics, ViolationDB, SessionLocal, clear_all_violations
)

from pydantic import BaseModel
from services.pipeline import process_image
from services.video_processor import VideoProcessor
from config import UPLOADS_DIR, EVIDENCE_DIR
from services.zone_manager import (
    get_all_zones, add_zone, update_zone, delete_zone as remove_zone
)
from schemas.api_schemas import ZoneConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])

VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


# ─── Upload & Processing ────────────────────────────────────

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a traffic image and run the full detection pipeline.
    Returns detections, violations, plates, and evidence path.
    For videos, use /api/upload-video instead.
    """
    # Validate file type
    ext = Path(file.filename or "upload.jpg").suffix.lower()
    if ext not in IMAGE_EXTENSIONS:
        raise HTTPException(400, f"File must be an image ({', '.join(IMAGE_EXTENSIONS)})")

    # Save uploaded file
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"upload_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
    filepath = UPLOADS_DIR / filename

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    logger.info(f"Uploaded image: {filepath} ({len(content)} bytes)")

    try:
        # Run pipeline in threadpool to avoid blocking async
        # Create a new session for the thread to be thread-safe with SQLite
        def _process():
            local_db = SessionLocal()
            try:
                return process_image(str(filepath), local_db)
            finally:
                local_db.close()
                
        result = await run_in_threadpool(_process)

        return JSONResponse({
            "success": True,
            "message": f"Processed {len(result.detections)} detections, "
                       f"{len(result.violations)} violations found",
            "result": result.model_dump(),
            "violations_count": len(result.violations),
        })
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        raise HTTPException(500, f"Processing failed: {str(e)}")


@router.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    frame_skip: int = Query(10, ge=1, le=30),
    location: str = Form("")
):
    """
    Upload a traffic video and process it frame-by-frame.
    Returns results as Server-Sent Events for real-time display.

    Each SSE event is a JSON object:
    - type="frame_result": annotated frame + detections + violations
    - type="complete": final summary stats
    """
    ext = Path(file.filename or "video.mp4").suffix.lower()
    if ext not in VIDEO_EXTENSIONS:
        raise HTTPException(400, f"File must be a video ({', '.join(VIDEO_EXTENSIONS)})")

    # Save uploaded video
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}{ext}"
    filepath = UPLOADS_DIR / filename

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    logger.info(f"Uploaded video: {filepath} ({len(content) / 1024 / 1024:.1f} MB)")

    def stream_results():
        """Generator that yields SSE events as the video is processed."""
        db = SessionLocal()
        try:
            processor = VideoProcessor(
                video_path=str(filepath),
                db=db,
                frame_skip=frame_skip,
                save_evidence=True,
                location=location,
            )

            # Send video info first
            try:
                info = processor.get_video_info()
                yield f"data: {json.dumps({'type': 'video_info', **info})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                return

            # Process frame by frame
            for result in processor.process_generator():
                yield f"data: {json.dumps(result)}\n\n"

        except Exception as e:
            logger.error(f"Video processing error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            db.close()

    return StreamingResponse(
        stream_results(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ─── Auth ──────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str




# ─── Database Reset ────────────────────────────────────────

@router.post("/reset")
async def reset_database(
    db: Session = Depends(get_db)
):
    """
    Clear all violation data for a fresh demo.
    Call this before showing judges to start clean.
    """
    count = clear_all_violations(db)
    return {
        "success": True,
        "message": f"Cleared {count} violations. Database is now empty for a fresh demo.",
        "cleared": count,
    }


# ─── Violations CRUD ────────────────────────────────────────

@router.get("/violations")
async def list_violations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None, alias="type"),
    plate: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List violations with pagination and filters."""
    violations, total = get_violations(
        db, page=page, per_page=per_page,
        violation_type=type, plate=plate,
        status=status,
        start_date=start_date, end_date=end_date,
    )

    return {
        "violations": [_serialize_violation(v) for v in violations],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.get("/violations/{violation_id}")
async def get_single_violation(
    violation_id: int,
    db: Session = Depends(get_db),
):
    """Get a single violation by ID."""
    v = get_violation_by_id(db, violation_id)
    if not v:
        raise HTTPException(404, "Violation not found")
    return _serialize_violation(v)


@router.delete("/violations/{violation_id}")
async def remove_violation(
    violation_id: int,
    db: Session = Depends(get_db)
):
    """Delete a violation record."""
    if delete_violation(db, violation_id):
        return {"success": True, "message": f"Violation #{violation_id} deleted"}
    raise HTTPException(404, "Violation not found")

class StatusUpdate(BaseModel):
    status: str

@router.post("/violations/{violation_id}/status")
async def update_violation_status(
    violation_id: int,
    payload: StatusUpdate,
    db: Session = Depends(get_db)
):
    """Update the status of a violation (e.g. issued, rejected)."""
    v = get_violation_by_id(db, violation_id)
    if not v:
        raise HTTPException(404, "Violation not found")
    
    if payload.status not in ["pending", "issued", "rejected"]:
        raise HTTPException(400, "Invalid status. Must be pending, issued, or rejected.")
        
    v.status = payload.status
    db.commit()
    return {"success": True, "status": v.status}



# ─── Analytics ───────────────────────────────────────────────

@router.get("/analytics")
async def analytics_summary(
    db: Session = Depends(get_db)
):
    """Get analytics summary for the dashboard."""
    data = get_analytics(db)
    # Serialize recent violations
    data["recent"] = [_serialize_violation(v) for v in data["recent"]]
    return data


# ─── Evidence ───────────────────────────────────────────────

@router.get("/evidence/{filename}")
async def serve_evidence(filename: str):
    """Serve an annotated evidence image."""
    filepath = EVIDENCE_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, "Evidence image not found")
    return FileResponse(str(filepath), media_type="image/jpeg")


@router.get("/uploads/{filename}")
async def serve_upload(filename: str):
    """Serve an uploaded image."""
    filepath = UPLOADS_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, "Upload not found")
    return FileResponse(str(filepath))


# ─── Zones ───────────────────────────────────────────────────

@router.get("/zones")
async def list_zones():
    """List all violation detection zones."""
    zones = get_all_zones()
    return {"zones": [z.model_dump() for z in zones]}


@router.post("/zones")
async def create_zone(zone: ZoneConfig):
    """Create a new violation detection zone."""
    created = add_zone(zone)
    return {"success": True, "zone": created.model_dump()}


@router.put("/zones/{zone_id}")
async def modify_zone(zone_id: str, updates: dict):
    """Update an existing zone."""
    updated = update_zone(zone_id, updates)
    if not updated:
        raise HTTPException(404, "Zone not found")
    return {"success": True, "zone": updated.model_dump()}


@router.delete("/zones/{zone_id}")
async def destroy_zone(zone_id: str):
    """Delete a zone."""
    if remove_zone(zone_id):
        return {"success": True, "message": f"Zone {zone_id} deleted"}
    raise HTTPException(404, "Zone not found")


# ─── System Info ─────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "AI Traffic Inspector",
    }


@router.get("/model-info")
async def model_info():
    """Get information about the loaded ML model."""
    try:
        from ml.detector import get_model_info
        info = await run_in_threadpool(get_model_info)
        return info
    except Exception as e:
        return {"error": str(e)}


@router.get("/supported-formats")
async def supported_formats():
    """Return supported upload formats."""
    return {
        "image": list(IMAGE_EXTENSIONS),
        "video": list(VIDEO_EXTENSIONS),
    }


# ─── Helpers ─────────────────────────────────────────────────

def _serialize_violation(v: ViolationDB) -> dict:
    """Convert a ViolationDB record to a JSON-serializable dict."""
    evidence_filename = ""
    if v.evidence_path:
        evidence_filename = Path(v.evidence_path).name

    image_filename = ""
    if v.image_path:
        image_filename = Path(v.image_path).name

    return {
        "id": v.id,
        "type": v.type,
        "confidence": v.confidence,
        "description": v.description,
        "plate_text": v.plate_text,
        "plate_confidence": v.plate_confidence,
        "timestamp": v.timestamp.isoformat() if v.timestamp else "",
        "image_path": image_filename,
        "image_url": f"/api/uploads/{image_filename}" if image_filename else "",
        "evidence_path": evidence_filename,
        "evidence_url": f"/api/evidence/{evidence_filename}" if evidence_filename else "",
        "zone_id": v.zone_id,
        "location": v.location,
        "status": v.status,
        "created_at": v.created_at.isoformat() if v.created_at else "",
    }
