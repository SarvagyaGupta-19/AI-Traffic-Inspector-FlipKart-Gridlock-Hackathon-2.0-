"""
AI Traffic Inspector — WebSocket Video Streaming
Real-time video frame processing over WebSocket.
"""
from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
from typing import Optional

import cv2
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from starlette.concurrency import run_in_threadpool

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.pipeline import process_frame
from config import MAX_STREAM_FPS

logger = logging.getLogger(__name__)

# Active WebSocket connections
active_connections: list = []


async def websocket_stream(websocket: WebSocket):
    """
    Handle WebSocket connection for real-time video streaming.

    Protocol:
    - Client sends video frames as base64-encoded JPEG/PNG
    - Server processes each frame and returns detection results
    - Client can send control messages (pause, resume, config)

    Message format (client → server):
    {
        "type": "frame",
        "data": "<base64-encoded-image>",
        "frame_number": 0
    }
    or
    {
        "type": "control",
        "action": "pause" | "resume" | "stop" | "config",
        "config": { ... }
    }

    Message format (server → client):
    {
        "type": "result",
        "frame_number": 0,
        "detections": [...],
        "violations": [...],
        "plates": [...],
        "processing_time_ms": 123.4,
        "annotated_frame": "<base64>" (optional)
    }
    """
    await websocket.accept()
    active_connections.append(websocket)
    logger.info(f"WebSocket connected. Total: {len(active_connections)}")

    frame_count = 0
    paused = False
    send_annotated = True
    frame_interval = 1.0 / MAX_STREAM_FPS

    db = SessionLocal()

    try:
        while True:
            # Receive message
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            msg_type = msg.get("type", "frame")

            # ─── Control messages ────────────────────────────
            if msg_type == "control":
                action = msg.get("action")
                if action == "pause":
                    paused = True
                    await websocket.send_json({"type": "status", "status": "paused"})
                    continue
                elif action == "resume":
                    paused = False
                    await websocket.send_json({"type": "status", "status": "streaming"})
                    continue
                elif action == "stop":
                    await websocket.send_json({"type": "status", "status": "stopped"})
                    break
                elif action == "config":
                    config = msg.get("config", {})
                    send_annotated = config.get("send_annotated", True)
                    continue

            if paused:
                continue

            # ─── Frame processing ────────────────────────────
            if msg_type == "frame":
                frame_data = msg.get("data", "")
                frame_number = msg.get("frame_number", frame_count)

                if not frame_data:
                    continue

                # Security: reject oversized frames (max ~10MB base64 = ~7.5MB image)
                if len(frame_data) > 10_000_000:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Frame too large (max 10MB)"
                    })
                    continue

                try:
                    # Decode base64 frame
                    frame_bytes = base64.b64decode(frame_data)
                    nparr = np.frombuffer(frame_bytes, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    if frame is None:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to decode frame"
                        })
                        continue

                    # Process frame in threadpool
                    result = await run_in_threadpool(
                        process_frame, frame, db, frame_number,
                        save_evidence=False, use_tracking=True
                    )

                    # Build response
                    response = {
                        "type": "result",
                        "frame_number": frame_number,
                        "detections": [d.model_dump() for d in result.detections],
                        "violations": [v.model_dump() for v in result.violations],
                        "plates": [p.model_dump() for p in result.plates],
                        "processing_time_ms": result.processing_time_ms,
                        "timestamp": result.timestamp,
                    }

                    # Optionally send annotated frame back
                    if send_annotated and (result.violations or result.detections):
                        from evidence.annotator import generate_evidence
                        annotated, _ = generate_evidence(frame, result, save=False)
                        _, buffer = cv2.imencode('.jpg', annotated,
                                                  [cv2.IMWRITE_JPEG_QUALITY, 70])
                        response["annotated_frame"] = base64.b64encode(
                            buffer.tobytes()
                        ).decode('utf-8')

                    await websocket.send_json(response)
                    frame_count += 1

                    # Rate limiting
                    await asyncio.sleep(frame_interval)

                except Exception as e:
                    logger.error(f"Frame processing error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                        "frame_number": frame_number,
                    })

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        db.close()
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"WebSocket cleaned up. Remaining: {len(active_connections)}")


async def broadcast_violation(violation_data: dict):
    """Broadcast a new violation to all connected clients."""
    message = json.dumps({
        "type": "violation_alert",
        "data": violation_data,
    })
    for ws in active_connections:
        try:
            await ws.send_text(message)
        except Exception:
            pass
