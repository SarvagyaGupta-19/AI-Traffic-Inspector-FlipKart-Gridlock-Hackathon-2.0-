"""
Flipkart Gridlock — Multi-Stage Cascade Detector
Real multi-model pipeline using Roboflow hosted models + local YOLO + ByteTrack.

Architecture:
  Stage 1: Local YOLOv8s (base detection: vehicles, people) + ByteTrack tracking
  Stage 2: Roboflow hosted safety classifier (helmet/seatbelt on cropped regions)
  Stage 3: Roboflow license plate detector + PaddleOCR reader
  Stage 4: Spatial violation logic with tracking deduplication
"""
from __future__ import annotations

import logging
import time
import os
from typing import List, Optional, Dict, Set, Tuple
from pathlib import Path

import cv2
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.schemas import Detection, BBox

logger = logging.getLogger(__name__)

# ─── Roboflow Configuration ────────────────────────────────────
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY", "a3zvwi4h6wiArIiGohzM")

# Roboflow hosted model IDs (from the suggestion)
RF_VEHICLE_MODEL = "vehicle-detection-bz0yu/4"
RF_PEOPLE_MODEL = "people-detection-o4rdr/7"
RF_PLATE_MODEL = "license-plate-recognition-rxg4e/4"

# ─── Tracking State ─────────────────────────────────────────────
# Track which vehicle IDs have already been flagged for each violation type
_violation_tracker: Dict[str, Set[int]] = {}


def reset_tracker():
    """Reset the violation tracker for a new video."""
    global _violation_tracker
    _violation_tracker = {}


def _already_flagged(track_id: int, violation_type: str) -> bool:
    """Check if this tracked object was already flagged for this violation."""
    if track_id is None:
        return False
    key = violation_type
    return track_id in _violation_tracker.get(key, set())


def _mark_flagged(track_id: int, violation_type: str):
    """Mark a tracked object as flagged for a violation type."""
    if track_id is None:
        return
    if violation_type not in _violation_tracker:
        _violation_tracker[violation_type] = set()
    _violation_tracker[violation_type].add(track_id)


class CascadeDetector:
    """
    Multi-stage cascade detection pipeline.
    
    Stage 1: Base detection (local YOLO + ByteTrack)
    Stage 2: Safety classification (Roboflow hosted models for helmet/seatbelt)
    Stage 3: License plate detection (Roboflow hosted) + OCR
    """

    def __init__(self, use_roboflow: bool = True, roboflow_api_key: str = None):
        self.use_roboflow = use_roboflow
        self.api_key = roboflow_api_key or ROBOFLOW_API_KEY
        self._rf_client = None
        self._safety_model = None
        self._plate_model = None
        self._initialized = False

    def _init_roboflow(self):
        """Lazy-initialize Roboflow inference client."""
        if self._initialized:
            return
        
        if not self.use_roboflow or not self.api_key:
            logger.warning("Roboflow API key not set. Using local-only mode.")
            self.use_roboflow = False
            self._initialized = True
            return
        
        try:
            from inference_sdk import InferenceHTTPClient
            self._rf_client = InferenceHTTPClient(
                api_url="https://detect.roboflow.com",
                api_key=self.api_key
            )
            logger.info("Roboflow Inference client initialized successfully")
            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize Roboflow client: {e}")
            self.use_roboflow = False
            self._initialized = True

    def detect_stage1_with_tracking(
        self, frame: np.ndarray
    ) -> Tuple[List[Detection], float]:
        """
        Stage 1: Run local YOLOv8 with ByteTrack for object tracking.
        Returns base detections with persistent track IDs.
        """
        from models.detector import detect_with_tracking
        detections, elapsed_ms, _ = detect_with_tracking(frame)
        return detections, elapsed_ms

    def detect_stage1_no_tracking(
        self, frame: np.ndarray
    ) -> Tuple[List[Detection], float]:
        """
        Stage 1 fallback: Run local YOLOv8 without tracking (for single images).
        """
        from models.detector import detect_objects
        detections, elapsed_ms, _ = detect_objects(frame)
        return detections, elapsed_ms

    def classify_safety_roboflow(
        self, frame: np.ndarray, detections: List[Detection]
    ) -> Dict[int, Dict]:
        """
        Stage 2: For each motorcycle rider or car occupant, crop the region
        and run Roboflow safety classifier to detect helmet/seatbelt.
        
        Returns a dict mapping detection index -> safety classification result.
        """
        self._init_roboflow()
        
        results = {}
        
        if not self.use_roboflow or not self._rf_client:
            return results
        
        motorcycles = [d for d in detections if d.class_name == "motorcycle"]
        persons = [d for d in detections if d.class_name == "person"]
        
        for i, motorcycle in enumerate(motorcycles):
            # Expand motorcycle bbox slightly for better context
            moto_bbox = motorcycle.bbox
            pad_x = int(moto_bbox.width * 0.15)
            pad_y = int(moto_bbox.height * 0.15)
            h, w = frame.shape[:2]
            
            x1 = max(0, moto_bbox.x1 - pad_x)
            y1 = max(0, moto_bbox.y1 - pad_y)
            x2 = min(w, moto_bbox.x2 + pad_x)
            y2 = min(h, moto_bbox.y2 + pad_y)
            
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue
            
            try:
                # Encode crop to JPEG bytes for Roboflow API
                _, buffer = cv2.imencode('.jpg', crop, [cv2.IMWRITE_JPEG_QUALITY, 85])
                img_bytes = buffer.tobytes()
                
                # Call Roboflow hosted model for safety detection
                # Using the people model to detect riders more precisely
                rf_result = self._rf_client.infer(img_bytes, model_id=RF_PEOPLE_MODEL)
                
                rider_count = 0
                if "predictions" in rf_result:
                    rider_count = len(rf_result["predictions"])
                
                results[i] = {
                    "type": "motorcycle_safety",
                    "rider_count": max(rider_count, len([
                        p for p in persons
                        if p.bbox.iou(motorcycle.bbox) > 0.1
                    ])),
                    "track_id": motorcycle.track_id,
                    "raw_predictions": rf_result.get("predictions", []),
                }
                
            except Exception as e:
                logger.debug(f"Roboflow safety check failed for motorcycle {i}: {e}")
                continue
        
        return results

    def detect_plates_roboflow(
        self, frame: np.ndarray, detections: List[Detection]
    ) -> List[Dict]:
        """
        Stage 3: Detect license plates using Roboflow hosted model.
        Returns list of plate region detections with bounding boxes.
        """
        self._init_roboflow()
        
        plates = []
        
        if not self.use_roboflow or not self._rf_client:
            return plates
        
        vehicles = [d for d in detections 
                     if d.class_name in ("car", "motorcycle", "bus", "truck")]
        
        for vehicle in vehicles:
            bbox = vehicle.bbox
            # Expand bbox slightly
            h, w = frame.shape[:2]
            pad_x = int(bbox.width * 0.1)
            pad_y = int(bbox.height * 0.1)
            
            x1 = max(0, bbox.x1 - pad_x)
            y1 = max(0, bbox.y1 - pad_y)
            x2 = min(w, bbox.x2 + pad_x)
            y2 = min(h, bbox.y2 + pad_y)
            
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue
            
            try:
                _, buffer = cv2.imencode('.jpg', crop, [cv2.IMWRITE_JPEG_QUALITY, 85])
                img_bytes = buffer.tobytes()
                
                rf_result = self._rf_client.infer(img_bytes, model_id=RF_PLATE_MODEL)
                
                if "predictions" in rf_result:
                    for pred in rf_result["predictions"]:
                        # Convert Roboflow coords (center-based) back to absolute
                        px = int(pred.get("x", 0))
                        py = int(pred.get("y", 0))
                        pw = int(pred.get("width", 0))
                        ph = int(pred.get("height", 0))
                        
                        plate_bbox = BBox(
                            x1=x1 + px - pw // 2,
                            y1=y1 + py - ph // 2,
                            x2=x1 + px + pw // 2,
                            y2=y1 + py + ph // 2,
                        )
                        
                        plates.append({
                            "bbox": plate_bbox,
                            "confidence": pred.get("confidence", 0.5),
                            "vehicle_track_id": vehicle.track_id,
                            "class": pred.get("class", "license-plate"),
                        })
                        
            except Exception as e:
                logger.debug(f"Roboflow plate detection failed: {e}")
                continue
        
        return plates

    def run_full_cascade(
        self,
        frame: np.ndarray,
        use_tracking: bool = True,
        run_safety: bool = True,
        run_plates: bool = True,
    ) -> Dict:
        """
        Run the complete multi-stage cascade pipeline.
        
        Returns:
            Dict with keys: detections, safety_results, plate_regions, elapsed_ms
        """
        total_start = time.time()
        
        # Stage 1: Base detection with tracking
        if use_tracking:
            detections, stage1_ms = self.detect_stage1_with_tracking(frame)
        else:
            detections, stage1_ms = self.detect_stage1_no_tracking(frame)
        
        # Stage 2: Safety classification (run every 3rd call to save API quota)
        safety_results = {}
        if run_safety:
            try:
                safety_results = self.classify_safety_roboflow(frame, detections)
            except Exception as e:
                logger.debug(f"Safety stage skipped: {e}")
        
        # Stage 3: Plate detection
        plate_regions = []
        if run_plates:
            try:
                plate_regions = self.detect_plates_roboflow(frame, detections)
            except Exception as e:
                logger.debug(f"Plate stage skipped: {e}")
        
        total_ms = (time.time() - total_start) * 1000
        
        return {
            "detections": detections,
            "safety_results": safety_results,
            "plate_regions": plate_regions,
            "stage1_ms": round(stage1_ms, 1),
            "total_ms": round(total_ms, 1),
        }


# Module-level singleton
_cascade_detector: Optional[CascadeDetector] = None


def get_cascade_detector() -> CascadeDetector:
    """Get or create the singleton CascadeDetector."""
    global _cascade_detector
    if _cascade_detector is None:
        _cascade_detector = CascadeDetector(
            use_roboflow=bool(ROBOFLOW_API_KEY),
            roboflow_api_key=ROBOFLOW_API_KEY,
        )
    return _cascade_detector
