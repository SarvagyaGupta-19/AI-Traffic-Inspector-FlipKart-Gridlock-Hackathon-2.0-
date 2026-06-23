"""
AI Traffic Inspector — YOLOv8 Detection Wrapper
Loads pretrained YOLOv8s and runs inference on traffic images.
Auto-detects GPU/CPU. Filters to traffic-relevant COCO classes.
"""
from __future__ import annotations

import time
import logging
from pathlib import Path
from typing import List, Optional, Union

import numpy as np

logger = logging.getLogger(__name__)

# Lazy import to avoid slow startup
_model = None


def _get_model(model_name: str = None):
    """Lazy-load the YOLO model (singleton pattern)."""
    global _model
    if _model is None:
        from ultralytics import YOLO
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from config import YOLO_MODEL

        model_path = model_name or YOLO_MODEL
        logger.info(f"Loading YOLO model: {model_path}")
        _model = YOLO(model_path)

        # Log device info
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"YOLO running on: {device}")
        if device == "cuda":
            logger.info(f"GPU: {torch.cuda.get_device_name(0)}")

    return _model


def detect_objects(
    image: Union[str, Path, np.ndarray],
    confidence: float = None,
    iou_threshold: float = None,
    img_size: int = None,
    filter_traffic: bool = True,
) -> tuple:
    """
    Run YOLO detection on an image.

    Args:
        image: File path or numpy array (BGR format from OpenCV)
        confidence: Override confidence threshold
        iou_threshold: Override IoU threshold for NMS
        img_size: Override input image size
        filter_traffic: If True, only return traffic-relevant classes

    Returns:
        Tuple of (list of Detection dicts, processing_time_ms, raw_results)
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config import (
        YOLO_CONFIDENCE, YOLO_IOU_THRESHOLD, YOLO_IMG_SIZE, TRAFFIC_CLASSES
    )
    from models.schemas import Detection, BBox

    conf = confidence or YOLO_CONFIDENCE
    iou = iou_threshold or YOLO_IOU_THRESHOLD
    size = img_size or YOLO_IMG_SIZE

    model = _get_model()

    start = time.time()
    results = model(
        image,
        conf=conf,
        iou=iou,
        imgsz=size,
        verbose=False,
    )
    elapsed_ms = (time.time() - start) * 1000

    detections: List[Detection] = []

    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue

        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].item())
            conf_score = float(boxes.conf[i].item())
            xyxy = boxes.xyxy[i].cpu().numpy().astype(int)

            # Filter to traffic-relevant classes if requested
            if filter_traffic and cls_id not in TRAFFIC_CLASSES:
                continue

            class_name = TRAFFIC_CLASSES.get(cls_id, result.names.get(cls_id, f"class_{cls_id}"))

            det = Detection(
                bbox=BBox(x1=int(xyxy[0]), y1=int(xyxy[1]), x2=int(xyxy[2]), y2=int(xyxy[3])),
                class_name=class_name,
                class_id=cls_id,
                confidence=round(conf_score, 3),
            )
            detections.append(det)

    logger.info(f"Detected {len(detections)} objects in {elapsed_ms:.1f}ms")
    return detections, elapsed_ms, results


def detect_with_tracking(
    image: Union[str, Path, np.ndarray],
    confidence: float = None,
    tracker: str = "bytetrack.yaml",
) -> tuple:
    """
    Run YOLO detection with object tracking (for video streams).

    Returns:
        Tuple of (list of Detection dicts, processing_time_ms, raw_results)
    """
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config import YOLO_CONFIDENCE, TRAFFIC_CLASSES
    from models.schemas import Detection, BBox

    conf = confidence or YOLO_CONFIDENCE
    model = _get_model()

    start = time.time()
    results = model.track(
        image,
        conf=conf,
        persist=True,
        tracker=tracker,
        verbose=False,
    )
    elapsed_ms = (time.time() - start) * 1000

    detections: List[Detection] = []

    for result in results:
        boxes = result.boxes
        if boxes is None:
            continue

        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].item())
            conf_score = float(boxes.conf[i].item())
            xyxy = boxes.xyxy[i].cpu().numpy().astype(int)

            if cls_id not in TRAFFIC_CLASSES:
                continue

            class_name = TRAFFIC_CLASSES.get(cls_id, f"class_{cls_id}")

            # Get tracking ID if available
            track_id = None
            if boxes.id is not None:
                track_id = int(boxes.id[i].item())

            det = Detection(
                bbox=BBox(x1=int(xyxy[0]), y1=int(xyxy[1]), x2=int(xyxy[2]), y2=int(xyxy[3])),
                class_name=class_name,
                class_id=cls_id,
                confidence=round(conf_score, 3),
                track_id=track_id,
            )
            detections.append(det)

    return detections, elapsed_ms, results


def get_model_info() -> dict:
    """Return model metadata for the API."""
    model = _get_model()
    import torch
    return {
        "model_name": model.model_name if hasattr(model, 'model_name') else str(model.model),
        "device": "cuda" if torch.cuda.is_available() else "cpu",
        "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "classes": list(model.names.values()) if hasattr(model, 'names') else [],
    }
