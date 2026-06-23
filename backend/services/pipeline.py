"""
AI Traffic Inspector — Detection Pipeline Orchestrator
Connects: Image → YOLO → Violation Logic → OCR → Evidence → DB
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from sqlalchemy.orm import Session

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemas.api_schemas import AnalysisResult, Violation
from ml.detector import detect_objects, detect_with_tracking
from services.violations import detect_all_violations
from services.zone_manager import get_active_zones
from ml.ocr.plate_reader import read_plates
from utils.annotator import generate_evidence
from core.database import store_violation
from services.preprocessor import preprocess_image, is_image_too_blurry
from config import UPLOADS_DIR

logger = logging.getLogger(__name__)


def process_image(
    image_path: str,
    db: Session,
    save_evidence: bool = True,
) -> AnalysisResult:
    """
    Full pipeline: process a single image through all stages.

    Args:
        image_path: Path to the input image
        db: Database session for storing violations
        save_evidence: Whether to generate and save evidence images

    Returns:
        Complete AnalysisResult
    """
    start_time = time.time()

    # ─── 1. Load image ───────────────────────────────────────
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")

    logger.info(f"Processing image: {image_path} ({image.shape[1]}x{image.shape[0]})")

    # ─── 1.5. Preprocess Image ───────────────────────────────
    if is_image_too_blurry(image):
        logger.warning(f"Image {image_path} is highly blurred. OCR confidence may be low.")
    
    image = preprocess_image(image)

    # ─── 2. Run YOLO detection ───────────────────────────────
    detections, detect_ms, raw_results = detect_objects(image)

    # ─── 3. Run violation logic ──────────────────────────────
    zones = get_active_zones()
    violations = detect_all_violations(detections, zones=zones, image=image)

    # ─── 4. Run OCR on detected plates ───────────────────────
    plates = read_plates(image, detections)

    # ─── 5. Associate plates with violations ─────────────────
    for violation in violations:
        if not violation.plate and plates:
            # Find the nearest plate to the violation's vehicle
            nearest_plate = _find_nearest_plate(violation, plates)
            if nearest_plate:
                violation.plate = nearest_plate

    total_ms = (time.time() - start_time) * 1000

    # ─── 6. Build result ─────────────────────────────────────
    result = AnalysisResult(
        image_path=str(image_path),
        detections=detections,
        violations=violations,
        plates=plates,
        processing_time_ms=round(total_ms, 1),
        timestamp=datetime.now().isoformat(),
    )

    # ─── 7. Generate evidence ────────────────────────────────
    if save_evidence and violations:
        _, evidence_path = generate_evidence(image, result, save=True)
        for violation in result.violations:
            violation.evidence_path = evidence_path
            violation.image_path = str(image_path)

    # ─── 8. Store violations in database ─────────────────────
    for violation in result.violations:
        store_violation(
            db=db,
            violation_type=violation.type.value,
            confidence=violation.confidence,
            description=violation.description,
            plate_text=violation.plate.text if violation.plate else None,
            plate_confidence=violation.plate.confidence if violation.plate else None,
            image_path=str(image_path),
            evidence_path=violation.evidence_path or "",
            detections=violation.detections,
            zone_id=violation.zone_id,
            timestamp=datetime.fromisoformat(violation.timestamp),
        )

    logger.info(
        f"Pipeline complete: {len(detections)} detections, "
        f"{len(violations)} violations, {len(plates)} plates, "
        f"{total_ms:.0f}ms total"
    )

    return result


def process_frame(
    frame: np.ndarray,
    db: Session,
    frame_number: int = 0,
    save_evidence: bool = False,
    use_tracking: bool = True,
) -> AnalysisResult:
    """
    Process a single video frame (for real-time streaming).
    Lighter weight than process_image — skips evidence gen by default.

    Args:
        frame: BGR numpy array
        db: Database session
        frame_number: Current frame number
        save_evidence: Whether to generate evidence images
        use_tracking: Use YOLO tracking (persistent IDs across frames)

    Returns:
        AnalysisResult
    """
    start_time = time.time()

    # Preprocess frame to handle low-light / noise
    frame = preprocess_image(frame)

    # Detection (with or without tracking)
    if use_tracking:
        detections, detect_ms, _ = detect_with_tracking(frame)
    else:
        detections, detect_ms, _ = detect_objects(frame)

    # Violations
    zones = get_active_zones()
    violations = detect_all_violations(detections, zones=zones, image=frame)

    # OCR (only run every few frames for performance)
    plates = []
    if frame_number % 5 == 0:  # OCR every 5th frame
        plates = read_plates(frame, detections)

    total_ms = (time.time() - start_time) * 1000

    result = AnalysisResult(
        image_path="stream",
        detections=detections,
        violations=violations,
        plates=plates,
        processing_time_ms=round(total_ms, 1),
        frame_number=frame_number,
        timestamp=datetime.now().isoformat(),
    )

    # Store violations (but not every frame — debounce)
    if violations and frame_number % 10 == 0:
        for violation in violations:
            # Associate nearest plate
            if not violation.plate and plates:
                violation.plate = _find_nearest_plate(violation, plates)

            store_violation(
                db=db,
                violation_type=violation.type.value,
                confidence=violation.confidence,
                description=violation.description,
                plate_text=violation.plate.text if violation.plate else None,
                plate_confidence=violation.plate.confidence if violation.plate else None,
                image_path="stream",
                frame_number=frame_number,
                timestamp=datetime.fromisoformat(violation.timestamp),
            )

    # Generate evidence on demand
    if save_evidence and violations:
        _, evidence_path = generate_evidence(frame, result, save=True)
        for v in result.violations:
            v.evidence_path = evidence_path

    return result


def _find_nearest_plate(violation: Violation, plates: list):
    """Find the closest plate to a violation's primary detection."""
    if not violation.detections or not plates:
        return None

    # Use the first vehicle detection in the violation
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

    # Only associate if plate is reasonably close
    max_dist = max(ref_bbox.width, ref_bbox.height) * 2
    return best_plate if best_dist < max_dist else None
