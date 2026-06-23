"""
AI Traffic Inspector - Video Processor
Processes uploaded video files frame-by-frame through the detection pipeline.
Yields annotated frames and results for real-time streaming back to the frontend.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import time
from pathlib import Path
from typing import AsyncGenerator, Optional

import cv2
import numpy as np
from sqlalchemy.orm import Session

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.detector import detect_objects
from schemas.api_schemas import AnalysisResult, Detection, Violation
from services.violations import detect_all_violations
from services.zone_manager import get_active_zones
from ml.ocr.plate_reader import read_plates
from utils.annotator import generate_evidence
from core.database import store_violation
from config import VIDEO_FRAME_WIDTH
from datetime import datetime

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Processes a video file frame-by-frame through the full detection pipeline.
    Designed for hackathon demo: shows real AI detections to judges.
    """

    def __init__(
        self,
        video_path: str,
        db: Session,
        frame_skip: int = 3,         # Process every Nth frame (skip 2)
        save_evidence: bool = True,
        max_frames: int = 0,          # 0 = no limit
        location: str = "",
    ):
        self.video_path = video_path
        self.db = db
        self.frame_skip = max(1, frame_skip)
        self.save_evidence = save_evidence
        self.max_frames = max_frames
        self.location = location

        # Stats
        self.total_frames = 0
        self.processed_frames = 0
        self.total_detections = 0
        self.total_violations = 0
        self.total_plates = 0
        self.start_time = 0.0
        self.is_running = False
        self.is_cancelled = False

    def cancel(self):
        """Cancel processing."""
        self.is_cancelled = True

    def get_video_info(self) -> dict:
        """Get video metadata before processing."""
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {self.video_path}")

        info = {
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "duration_sec": 0.0,
        }
        if info["fps"] > 0:
            info["duration_sec"] = round(info["total_frames"] / info["fps"], 1)

        cap.release()
        return info

    def process_sync(self) -> list[dict]:
        """
        Synchronous processing - processes all frames and returns results.
        Used by the REST upload endpoint.
        """
        results = []
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {self.video_path}")

        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.start_time = time.time()
        self.is_running = True
        frame_idx = 0

        try:
            while cap.isOpened() and not self.is_cancelled:
                ret, frame = cap.read()
                if not ret:
                    break

                if self.max_frames > 0 and self.processed_frames >= self.max_frames:
                    break

                # Skip frames for performance
                if frame_idx % self.frame_skip != 0:
                    frame_idx += 1
                    continue

                # Resize for faster processing
                frame = self._resize_frame(frame)

                # Run full pipeline
                result = self._process_single_frame(frame, frame_idx)
                if result:
                    results.append(result)

                frame_idx += 1

        finally:
            cap.release()
            self.is_running = False

        return results

    def process_generator(self):
        """
        Generator that yields frame-by-frame results for streaming.
        Each yield is a dict with the annotated frame (base64) + detections.
        """
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {self.video_path}")

        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.start_time = time.time()
        self.is_running = True
        frame_idx = 0

        # Reset cascade tracker for new video
        try:
            from ml.cascade_detector import reset_tracker
            reset_tracker()
        except ImportError:
            pass

        try:
            while cap.isOpened() and not self.is_cancelled:
                ret, frame = cap.read()
                if not ret:
                    break

                if self.max_frames > 0 and self.processed_frames >= self.max_frames:
                    break

                # Skip frames for performance
                if frame_idx % self.frame_skip != 0:
                    frame_idx += 1
                    continue

                # Resize for faster processing
                frame = self._resize_frame(frame)

                # Process
                result = self._process_single_frame(frame, frame_idx)

                if result:
                    # Generate annotated frame
                    annotated_b64 = self._frame_to_base64(result["annotated_frame"])

                    yield {
                        "type": "frame_result",
                        "frame_number": frame_idx,
                        "progress": round(frame_idx / max(self.total_frames, 1) * 100, 1),
                        "detections": result["detections"],
                        "violations": result["violations"],
                        "plates": result["plates"],
                        "processing_time_ms": result["processing_time_ms"],
                        "annotated_frame": annotated_b64,
                        "stats": self._get_stats(),
                    }

                frame_idx += 1

        finally:
            cap.release()
            self.is_running = False

        # Final summary
        yield {
            "type": "complete",
            "stats": self._get_stats(),
        }

    def _process_single_frame(self, frame: np.ndarray, frame_idx: int) -> Optional[dict]:
        """
        Process a single frame through the multi-stage cascade pipeline.
        
        Stage 1: YOLOv8 + ByteTrack (local, fast)
        Stage 2: Roboflow safety classifier (hosted, on crops)
        Stage 3: OCR on detected plate regions
        Stage 4: Spatial violation logic with tracking deduplication
        """
        start = time.time()

        try:
            from ml.cascade_detector import (
                get_cascade_detector, _already_flagged, _mark_flagged
            )
            
            cascade = get_cascade_detector()
            
            # Run every 5th frame through Roboflow to save API quota
            run_rf_safety = (self.processed_frames % 5 == 0)
            run_rf_plates = (self.processed_frames % 3 == 0)
            
            # ── Stage 1: Base detection with ByteTrack ──
            cascade_result = cascade.run_full_cascade(
                frame,
                use_tracking=True,
                run_safety=run_rf_safety,
                run_plates=run_rf_plates,
            )
            
            detections = cascade_result["detections"]
            
            # ── Stage 2+4: Violation logic with tracking deduplication ──
            zones = get_active_zones()
            violations = detect_all_violations(detections, zones=zones, image=frame)
            
            # Deduplicate: skip violations for already-flagged track IDs
            unique_violations = []
            for v in violations:
                # Find the primary vehicle/person track_id for this violation
                track_ids = [d.track_id for d in v.detections if d.track_id is not None]
                primary_track = track_ids[0] if track_ids else None
                
                if primary_track and _already_flagged(primary_track, v.type.value):
                    continue  # Skip — already logged for this vehicle
                
                unique_violations.append(v)
                if primary_track:
                    _mark_flagged(primary_track, v.type.value)
            
            violations = unique_violations

            # ── Stage 3: OCR on plates ──
            plates = []
            if self.processed_frames % 3 == 0:
                plates = read_plates(frame, detections)

            processing_ms = (time.time() - start) * 1000

            # Build AnalysisResult for evidence generation
            analysis = AnalysisResult(
                image_path=self.video_path,
                detections=detections,
                violations=violations,
                plates=plates,
                processing_time_ms=round(processing_ms, 1),
                frame_number=frame_idx,
                timestamp=datetime.now().isoformat(),
            )

            # Generate annotated frame (always, for live display)
            annotated, evidence_path = generate_evidence(
                frame, analysis, save=self.save_evidence and bool(violations)
            )

            # Store violations in DB (real data!)
            for violation in violations:
                # Associate nearest plate
                if not violation.plate and plates:
                    violation.plate = self._find_nearest_plate(violation, plates)

                store_violation(
                    db=self.db,
                    violation_type=violation.type.value,
                    confidence=violation.confidence,
                    description=violation.description,
                    plate_text=violation.plate.text if violation.plate else None,
                    plate_confidence=violation.plate.confidence if violation.plate else None,
                    image_path=self.video_path,
                    evidence_path=evidence_path or "",
                    detections=violation.detections,
                    zone_id=violation.zone_id,
                    frame_number=frame_idx,
                    location=self.location,
                    timestamp=datetime.fromisoformat(violation.timestamp),
                )

            # Update stats
            self.processed_frames += 1
            self.total_detections += len(detections)
            self.total_violations += len(violations)
            self.total_plates += len(plates)

            return {
                "detections": [d.model_dump() for d in detections],
                "violations": [v.model_dump() for v in violations],
                "plates": [p.model_dump() for p in plates],
                "processing_time_ms": round(processing_ms, 1),
                "annotated_frame": annotated,
                "evidence_path": evidence_path,
                "cascade_stages": {
                    "stage1_ms": cascade_result["stage1_ms"],
                    "total_cascade_ms": cascade_result["total_ms"],
                    "rf_safety_ran": run_rf_safety,
                    "rf_plates_ran": run_rf_plates,
                },
            }

        except Exception as e:
            logger.error(f"Frame {frame_idx} processing error: {e}", exc_info=True)
            self.processed_frames += 1
            return None

    def _resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame to target width for consistent processing speed."""
        h, w = frame.shape[:2]
        if w > VIDEO_FRAME_WIDTH:
            scale = VIDEO_FRAME_WIDTH / w
            new_w = VIDEO_FRAME_WIDTH
            new_h = int(h * scale)
            return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return frame

    def _frame_to_base64(self, frame: np.ndarray) -> str:
        """Encode frame as JPEG base64."""
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
        return base64.b64encode(buffer.tobytes()).decode('utf-8')

    def _find_nearest_plate(self, violation: Violation, plates: list):
        """Find closest plate to a violation's vehicle detection."""
        if not violation.detections or not plates:
            return None

        vehicle_dets = [d for d in violation.detections
                        if d.class_name in ("car", "motorcycle", "bus", "truck")]
        if not vehicle_dets:
            vehicle_dets = violation.detections

        ref_bbox = vehicle_dets[0].bbox
        ref_cx, ref_cy = ref_bbox.center

        best_plate = None
        best_dist = float("inf")

        for plate in plates:
            px, py = plate.bbox.center
            dist = ((px - ref_cx) ** 2 + (py - ref_cy) ** 2) ** 0.5
            if dist < best_dist:
                best_dist = dist
                best_plate = plate

        max_dist = max(ref_bbox.width, ref_bbox.height) * 2
        return best_plate if best_dist < max_dist else None

    def _get_stats(self) -> dict:
        """Get current processing stats."""
        elapsed = time.time() - self.start_time if self.start_time else 0
        return {
            "total_frames": self.total_frames,
            "processed_frames": self.processed_frames,
            "total_detections": self.total_detections,
            "total_violations": self.total_violations,
            "total_plates": self.total_plates,
            "elapsed_sec": round(elapsed, 1),
            "fps": round(self.processed_frames / elapsed, 1) if elapsed > 0 else 0,
            "progress_pct": round(
                self.processed_frames * self.frame_skip / max(self.total_frames, 1) * 100, 1
            ),
        }
