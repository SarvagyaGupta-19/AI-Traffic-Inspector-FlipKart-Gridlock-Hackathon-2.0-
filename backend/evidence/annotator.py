"""
Flipkart Gridlock — Evidence Annotator
Generates judge-ready annotated evidence images with bounding boxes,
violation labels, confidence scores, plate text, and timestamps.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.schemas import Detection, Violation, PlateResult, AnalysisResult
from config import EVIDENCE_DIR, EVIDENCE_BOX_COLORS, EVIDENCE_WATERMARK

logger = logging.getLogger(__name__)


def generate_evidence(
    image: np.ndarray,
    result: AnalysisResult,
    save: bool = True,
) -> tuple:
    """
    Generate an annotated evidence image from analysis results.

    Args:
        image: Original BGR image
        result: Complete analysis result
        save: Whether to save to disk

    Returns:
        Tuple of (annotated_image, evidence_path)
    """
    annotated = image.copy()
    h, w = annotated.shape[:2]

    # ─── 1. Draw header bar ──────────────────────────────────
    annotated = _draw_header(annotated, result)

    # ─── 2. Draw all detections (non-violation) ──────────────
    violation_det_ids = set()
    for v in result.violations:
        for d in v.detections:
            violation_det_ids.add(id(d))

    for det in result.detections:
        if id(det) not in violation_det_ids:
            _draw_detection(annotated, det, color=EVIDENCE_BOX_COLORS["detection"])

    # ─── 3. Draw violation detections ────────────────────────
    for violation in result.violations:
        _draw_violation(annotated, violation)

    # ─── 4. Draw license plates ──────────────────────────────
    for plate in result.plates:
        _draw_plate(annotated, plate)

    # ─── 5. Draw timestamp watermark ─────────────────────────
    annotated = _draw_timestamp(annotated, result.timestamp)

    # ─── 6. Draw footer with processing info ─────────────────
    annotated = _draw_footer(annotated, result)

    # ─── 7. Save evidence ────────────────────────────────────
    evidence_path = None
    if save:
        evidence_path = _save_evidence(annotated)

    return annotated, evidence_path


def _draw_header(image: np.ndarray, result: AnalysisResult) -> np.ndarray:
    """Draw a header bar with violation summary."""
    h, w = image.shape[:2]
    header_h = 50

    # Create header
    header = np.zeros((header_h, w, 3), dtype=np.uint8)

    if result.violations:
        # Red gradient header for violations
        header[:, :] = (30, 20, 60)  # Dark red-ish background
        status_text = f"[!] {len(result.violations)} VIOLATION(S) DETECTED"
        status_color = (80, 80, 255)  # Red
    else:
        header[:, :] = (60, 40, 20)  # Dark blue-ish background
        status_text = "[OK] NO VIOLATIONS DETECTED"
        status_color = (80, 200, 80)  # Green

    # Draw "GRIDLOCK EVIDENCE" watermark
    cv2.putText(header, EVIDENCE_WATERMARK, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

    # Draw violation count
    text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
    cv2.putText(header, status_text, (w - text_size[0] - 10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)

    return np.vstack([header, image])


def _draw_detection(
    image: np.ndarray,
    det: Detection,
    color: tuple = (255, 214, 10),
    offset_y: int = 50,
):
    """Draw a single detection bounding box."""
    bbox = det.bbox
    y1 = bbox.y1 + offset_y  # Account for header

    cv2.rectangle(image, (bbox.x1, y1), (bbox.x2, bbox.y2 + offset_y),
                  color, 1)

    label = f"{det.class_name} {det.confidence:.0%}"
    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]

    # Label background
    cv2.rectangle(image,
                  (bbox.x1, y1 - label_size[1] - 6),
                  (bbox.x1 + label_size[0] + 4, y1),
                  color, -1)
    cv2.putText(image, label, (bbox.x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)


def _draw_violation(image: np.ndarray, violation: Violation, offset_y: int = 50):
    """Draw violation bounding boxes with prominent labeling."""
    color = EVIDENCE_BOX_COLORS["violation"]

    # Violation type labels
    type_labels = {
        "helmet_missing": "NO HELMET",
        "seatbelt_missing": "NO SEATBELT",
        "triple_riding": "TRIPLE RIDING",
        "wrong_side": "WRONG SIDE",
        "stop_line": "STOP LINE VIOLATION",
        "red_light": "RED LIGHT VIOLATION",
        "illegal_parking": "ILLEGAL PARKING",
    }

    label = type_labels.get(violation.type.value, violation.type.value.upper())

    for det in violation.detections:
        bbox = det.bbox
        y1 = bbox.y1 + offset_y
        y2 = bbox.y2 + offset_y

        # Thick red border for violations
        cv2.rectangle(image, (bbox.x1, y1), (bbox.x2, y2), color, 3)

        # Corner markers for emphasis
        corner_len = min(20, bbox.width // 4, bbox.height // 4)
        # Top-left
        cv2.line(image, (bbox.x1, y1), (bbox.x1 + corner_len, y1), color, 4)
        cv2.line(image, (bbox.x1, y1), (bbox.x1, y1 + corner_len), color, 4)
        # Top-right
        cv2.line(image, (bbox.x2, y1), (bbox.x2 - corner_len, y1), color, 4)
        cv2.line(image, (bbox.x2, y1), (bbox.x2, y1 + corner_len), color, 4)
        # Bottom-left
        cv2.line(image, (bbox.x1, y2), (bbox.x1 + corner_len, y2), color, 4)
        cv2.line(image, (bbox.x1, y2), (bbox.x1, y2 - corner_len), color, 4)
        # Bottom-right
        cv2.line(image, (bbox.x2, y2), (bbox.x2 - corner_len, y2), color, 4)
        cv2.line(image, (bbox.x2, y2), (bbox.x2, y2 - corner_len), color, 4)

    # Draw violation label at the top of the first detection
    if violation.detections:
        first_det = violation.detections[0]
        label_text = f"{label} ({violation.confidence:.0%})"
        label_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)[0]

        lx = first_det.bbox.x1
        ly = first_det.bbox.y1 + offset_y - 10

        # Label background with padding
        cv2.rectangle(image,
                      (lx - 2, ly - label_size[1] - 8),
                      (lx + label_size[0] + 6, ly + 4),
                      color, -1)
        cv2.putText(image, label_text, (lx + 2, ly - 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)


def _draw_plate(image: np.ndarray, plate: PlateResult, offset_y: int = 50):
    """Draw license plate detection with OCR text."""
    color = EVIDENCE_BOX_COLORS["plate"]
    bbox = plate.bbox
    y1 = bbox.y1 + offset_y
    y2 = bbox.y2 + offset_y

    # Blue box for plate
    cv2.rectangle(image, (bbox.x1, y1), (bbox.x2, y2), color, 2)

    # Plate text label below the box
    plate_text = f"PLATE: {plate.text} ({plate.confidence:.0%})"
    label_size = cv2.getTextSize(plate_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]

    cv2.rectangle(image,
                  (bbox.x1, y2),
                  (bbox.x1 + label_size[0] + 6, y2 + label_size[1] + 8),
                  color, -1)
    cv2.putText(image, plate_text, (bbox.x1 + 3, y2 + label_size[1] + 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


def _draw_timestamp(image: np.ndarray, timestamp: str) -> np.ndarray:
    """Draw timestamp watermark in bottom-right corner."""
    h, w = image.shape[:2]

    try:
        dt = datetime.fromisoformat(timestamp)
        ts_text = dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        ts_text = timestamp

    text_size = cv2.getTextSize(ts_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
    tx = w - text_size[0] - 15
    ty = h - 15

    # Semi-transparent background
    overlay = image.copy()
    cv2.rectangle(overlay, (tx - 5, ty - text_size[1] - 5),
                  (w - 5, ty + 5), (0, 0, 0), -1)
    image = cv2.addWeighted(overlay, 0.6, image, 0.4, 0)

    cv2.putText(image, ts_text, (tx, ty),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    return image


def _draw_footer(image: np.ndarray, result: AnalysisResult) -> np.ndarray:
    """Draw a footer with processing metadata."""
    h, w = image.shape[:2]
    footer_h = 30

    footer = np.zeros((footer_h, w, 3), dtype=np.uint8)
    footer[:, :] = (30, 30, 30)

    info = (
        f"Objects: {len(result.detections)} | "
        f"Violations: {len(result.violations)} | "
        f"Plates: {len(result.plates)} | "
        f"Processing: {result.processing_time_ms:.0f}ms | "
        f"Flipkart Gridlock"
    )

    cv2.putText(footer, info, (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (160, 160, 160), 1)

    return np.vstack([image, footer])


def _save_evidence(image: np.ndarray) -> str:
    """Save evidence image and return the file path."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    uid = uuid.uuid4().hex[:8]
    filename = f"evidence_{timestamp}_{uid}.jpg"
    filepath = EVIDENCE_DIR / filename

    cv2.imwrite(str(filepath), image, [cv2.IMWRITE_JPEG_QUALITY, 92])
    logger.info(f"Evidence saved: {filepath}")

    return str(filepath)


def generate_thumbnail(image: np.ndarray, max_size: int = 300) -> np.ndarray:
    """Generate a thumbnail for the dashboard."""
    h, w = image.shape[:2]
    scale = max_size / max(h, w)
    if scale < 1:
        return cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return image
