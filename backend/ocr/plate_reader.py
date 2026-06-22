"""
Flipkart Gridlock — License Plate Reader
PaddleOCR-based pipeline for Indian number plate detection and text extraction.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.schemas import PlateResult, BBox, Detection
from config import (
    OCR_LANG, OCR_USE_ANGLE_CLS, INDIAN_PLATE_REGEX, OCR_MIN_CONFIDENCE, FAST_OCR_MODE
)

logger = logging.getLogger(__name__)

# Lazy-loaded OCR engine
_ocr_engine = None


def _get_ocr():
    """Lazy-load PaddleOCR engine."""
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from paddleocr import PaddleOCR
            _ocr_engine = PaddleOCR(
                use_angle_cls=OCR_USE_ANGLE_CLS,
                lang=OCR_LANG,
                show_log=False,
            )
            logger.info("PaddleOCR engine initialized")
        except ImportError:
            logger.warning("PaddleOCR not installed. OCR will be disabled.")
            return None
        except Exception as e:
            logger.warning(f"PaddleOCR initialization failed: {e}")
            return None
    return _ocr_engine


def read_plates(
    image: np.ndarray,
    detections: List[Detection],
) -> List[PlateResult]:
    """
    Detect and read license plates from an image.

    Strategy:
    1. Look for plate-like regions near detected vehicles
    2. If YOLO detected something that could be a plate, crop and OCR it
    3. Fall back to contour-based plate detection if needed

    Args:
        image: BGR numpy array
        detections: YOLO detections (to find vehicle regions)
        fast_mode: If True, skips full-image fallback (use for video)

    Returns:
        List of PlateResult with text and confidence
    """
    plates = []
    
    # Check if fast_mode overrides global setting
    try:
        from config import FAST_OCR_MODE
        fast_mode = FAST_OCR_MODE
    except ImportError:
        fast_mode = False

    # Get vehicle detections
    vehicles = [d for d in detections if d.class_name in ("car", "motorcycle", "bus", "truck")]

    for vehicle in vehicles:
        # Try to find plate in the lower half of the vehicle bbox
        plate_region = _get_plate_region(vehicle.bbox, image.shape)

        # Crop the plate search region
        crop = image[plate_region.y1:plate_region.y2, plate_region.x1:plate_region.x2]
        if crop.size == 0:
            continue

        # Try contour-based plate detection first
        plate_crops = _find_plate_contours(crop)

        if not plate_crops:
            # Use the entire lower region as fallback
            plate_crops = [(crop, BBox(
                x1=plate_region.x1, y1=plate_region.y1,
                x2=plate_region.x2, y2=plate_region.y2
            ))]

        for plate_img, plate_bbox in plate_crops:
            # Try GLM-OCR (Gemini Vision) first for higher accuracy
            try:
                from ocr.glm_ocr import read_plate_glm
                glm_result = read_plate_glm(plate_img)
                if glm_result and glm_result.get("confidence", 0) >= OCR_MIN_CONFIDENCE:
                    plates.append(PlateResult(
                        text=glm_result["text"],
                        confidence=glm_result["confidence"],
                        bbox=plate_bbox,
                        raw_text=glm_result.get("raw_response", glm_result["text"]),
                    ))
                    logger.info(f"GLM-OCR read plate: {glm_result['text']}")
                    continue  # Got it from Gemini, skip PaddleOCR
            except Exception as e:
                logger.debug(f"GLM-OCR skipped: {e}")

            # Fallback to PaddleOCR
            result = _ocr_plate(plate_img, plate_bbox)
            if result and result.confidence >= OCR_MIN_CONFIDENCE:
                plates.append(result)

    # Also try full-image OCR for any visible plates not near vehicles
    if not plates and not fast_mode:
        full_result = _ocr_full_image(image)
        plates.extend(full_result)

    logger.info(f"Found {len(plates)} license plates")
    return plates


def _get_plate_region(vehicle_bbox: BBox, image_shape: Tuple[int, ...]) -> BBox:
    """Get the region where a plate is likely located (lower 40% of vehicle)."""
    img_h, img_w = image_shape[:2]

    # Plates are typically in the lower portion and slightly extended horizontally
    y1 = vehicle_bbox.y1 + int(vehicle_bbox.height * 0.5)
    y2 = min(vehicle_bbox.y2 + int(vehicle_bbox.height * 0.1), img_h)
    x1 = max(vehicle_bbox.x1 - int(vehicle_bbox.width * 0.05), 0)
    x2 = min(vehicle_bbox.x2 + int(vehicle_bbox.width * 0.05), img_w)

    return BBox(x1=x1, y1=y1, x2=x2, y2=y2)


def _find_plate_contours(region: np.ndarray) -> List[Tuple[np.ndarray, BBox]]:
    """
    Find plate-like rectangular contours in a region.
    Indian plates have roughly 4.5:1 aspect ratio (long) or 2:1 (square type).
    """
    results = []

    try:
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)

        # Adaptive threshold to handle varying lighting
        thresh = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 500:  # Too small
                continue

            # Approximate polygon
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

            # Plates are roughly rectangular (4 corners)
            if len(approx) >= 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect = w / h if h > 0 else 0

                # Indian plates: long format (~4.5:1) or square (~2:1)
                if (1.5 <= aspect <= 6.0) and (w > 60) and (h > 15):
                    plate_crop = region[y:y + h, x:x + w]
                    plate_bbox = BBox(x1=x, y1=y, x2=x + w, y2=y + h)
                    results.append((plate_crop, plate_bbox))

        # Sort by area (largest first) and keep top 3
        results.sort(key=lambda r: r[1].area, reverse=True)
        return results[:3]

    except Exception as e:
        logger.debug(f"Contour detection failed: {e}")
        return []


def _preprocess_plate(plate_img: np.ndarray) -> np.ndarray:
    """Preprocess plate image for better OCR accuracy."""
    try:
        # Resize to consistent height
        target_h = 64
        scale = target_h / plate_img.shape[0]
        resized = cv2.resize(plate_img, None, fx=scale, fy=scale,
                             interpolation=cv2.INTER_CUBIC)

        # Convert to grayscale
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        # Enhance contrast with CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)

        # Threshold
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        return binary
    except Exception:
        return plate_img


def _ocr_plate(plate_img: np.ndarray, bbox: BBox) -> Optional[PlateResult]:
    """Run OCR on a single plate crop."""
    ocr = _get_ocr()
    if ocr is None:
        return None

    try:
        # Preprocess
        processed = _preprocess_plate(plate_img)

        # Run OCR
        results = ocr.ocr(processed, cls=True)

        if not results or not results[0]:
            return None

        # Combine all detected text lines
        texts = []
        confidences = []
        for line in results[0]:
            if line and len(line) >= 2:
                text = line[1][0]
                conf = line[1][1]
                texts.append(text)
                confidences.append(conf)

        if not texts:
            return None

        raw_text = " ".join(texts)
        cleaned = _clean_plate_text(raw_text)
        avg_confidence = float(np.mean(confidences))

        return PlateResult(
            text=cleaned,
            confidence=round(avg_confidence, 3),
            bbox=bbox,
            raw_text=raw_text,
        )

    except Exception as e:
        logger.debug(f"OCR failed: {e}")
        return None


def _ocr_full_image(image: np.ndarray) -> List[PlateResult]:
    """Run OCR on the full image to catch any missed plates."""
    ocr = _get_ocr()
    if ocr is None:
        return []

    try:
        results = ocr.ocr(image, cls=True)
        plates = []

        if not results or not results[0]:
            return []

        for line in results[0]:
            if line and len(line) >= 2:
                text = line[1][0]
                conf = line[1][1]
                cleaned = _clean_plate_text(text)

                # Check if it matches Indian plate format
                if _is_valid_plate(cleaned) and conf >= OCR_MIN_CONFIDENCE:
                    # Get bbox from OCR detection points
                    points = line[0]
                    x_coords = [p[0] for p in points]
                    y_coords = [p[1] for p in points]

                    plates.append(PlateResult(
                        text=cleaned,
                        confidence=round(conf, 3),
                        bbox=BBox(
                            x1=int(min(x_coords)),
                            y1=int(min(y_coords)),
                            x2=int(max(x_coords)),
                            y2=int(max(y_coords)),
                        ),
                        raw_text=text,
                    ))

        return plates

    except Exception as e:
        logger.debug(f"Full-image OCR failed: {e}")
        return []


def _clean_plate_text(text: str) -> str:
    """Clean and normalize plate text."""
    # Remove special characters except alphanumeric and spaces
    cleaned = re.sub(r'[^A-Za-z0-9\s]', '', text.upper())

    # Common OCR substitutions for Indian plates
    substitutions = {
        'O': '0',  # Only in numeric positions
        'I': '1',
        'S': '5',
        'Z': '2',
        'B': '8',
    }

    # Remove extra spaces
    cleaned = ' '.join(cleaned.split())

    return cleaned


def _is_valid_plate(text: str) -> bool:
    """Check if text matches Indian plate format."""
    # Remove spaces for regex matching
    no_spaces = text.replace(' ', '')

    # Indian format: XX00XX0000 or XX00X0000 (no spaces variant)
    if re.match(r'^[A-Z]{2}\d{1,2}[A-Z]{1,3}\d{4}$', no_spaces):
        return True

    # Partial match: at least 2 letters followed by numbers
    if re.match(r'^[A-Z]{2}\d{2}', no_spaces) and len(no_spaces) >= 6:
        return True

    return False
