"""
AI Traffic Inspector — GLM-OCR (Gemini Vision License Plate Reader)
Uses Google's Gemini Vision API as a Vision-Language Model for high-accuracy
license plate text extraction from cropped plate images.

Falls back to PaddleOCR if Gemini is unavailable or times out.
"""
from __future__ import annotations

import base64
import logging
import re
import time
from typing import Optional

import cv2
import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import GEMINI_API_KEY, INDIAN_PLATE_REGEX

logger = logging.getLogger(__name__)

# Singleton client
_gemini_client = None
_gemini_available = None


def _get_gemini_client():
    """Lazy-initialize the Gemini client."""
    global _gemini_client, _gemini_available

    if _gemini_available is False:
        return None

    if _gemini_client is not None:
        return _gemini_client

    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set. GLM-OCR disabled.")
        _gemini_available = False
        return None

    try:
        from google import genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        _gemini_available = True
        logger.info("Gemini Vision client initialized for GLM-OCR")
        return _gemini_client
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        _gemini_available = False
        return None


def read_plate_glm(plate_crop: np.ndarray, timeout: float = 5.0) -> Optional[dict]:
    """
    Use Gemini Vision to read a license plate from a cropped image.

    Args:
        plate_crop: BGR numpy array of the cropped license plate region
        timeout: Maximum seconds to wait for API response

    Returns:
        Dict with 'text' and 'confidence' if plate found, else None
    """
    client = _get_gemini_client()
    if client is None:
        return None

    try:
        # Encode crop to JPEG base64
        _, buffer = cv2.imencode('.jpg', plate_crop, [cv2.IMWRITE_JPEG_QUALITY, 90])
        img_b64 = base64.b64encode(buffer.tobytes()).decode('utf-8')

        start = time.time()

        # Call Gemini Vision with a very specific prompt
        from google.genai import types

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Content(
                    parts=[
                        types.Part(
                            inline_data=types.Blob(
                                mime_type="image/jpeg",
                                data=buffer.tobytes()
                            )
                        ),
                        types.Part(
                            text=(
                                "You are a license plate OCR system for Indian traffic enforcement. "
                                "Read the license plate number from this image. "
                                "Indian plates follow the format: XX00XX0000 (e.g., KA01AB1234). "
                                "Return ONLY the plate text in uppercase with no spaces, no explanation. "
                                "If you cannot read the plate clearly, return 'UNREADABLE'."
                            )
                        ),
                    ]
                )
            ],
        )

        elapsed = time.time() - start
        logger.debug(f"Gemini OCR took {elapsed:.1f}s")

        if response and response.text:
            raw_text = response.text.strip().upper()

            # Clean up the response
            # Remove any markdown, quotes, or extra text
            raw_text = raw_text.replace("`", "").replace("'", "").replace('"', '')
            raw_text = raw_text.split('\n')[0].strip()

            if raw_text == "UNREADABLE" or len(raw_text) < 4:
                return None

            # Remove spaces for matching
            clean_text = re.sub(r'\s+', '', raw_text)

            # Validate against Indian plate pattern
            plate_pattern = re.compile(INDIAN_PLATE_REGEX)
            if plate_pattern.match(clean_text):
                return {
                    "text": clean_text,
                    "confidence": 0.92,  # High confidence for Gemini reads
                    "source": "gemini_vision",
                    "raw_response": raw_text,
                }

            # Even if it doesn't match the strict regex, return it if it looks like a plate
            if len(clean_text) >= 6 and any(c.isdigit() for c in clean_text):
                return {
                    "text": clean_text,
                    "confidence": 0.75,
                    "source": "gemini_vision",
                    "raw_response": raw_text,
                }

        return None

    except Exception as e:
        logger.debug(f"Gemini OCR failed: {e}")
        return None


def read_plate_with_fallback(
    plate_crop: np.ndarray,
    detections: list = None,
) -> Optional[dict]:
    """
    Try Gemini Vision first, fall back to PaddleOCR.

    Args:
        plate_crop: BGR numpy array of the cropped plate region
        detections: Optional YOLO detections for context

    Returns:
        Dict with 'text', 'confidence', 'source' or None
    """
    # Try Gemini Vision first (more accurate for Indian plates)
    result = read_plate_glm(plate_crop)
    if result:
        logger.info(f"GLM-OCR read plate: {result['text']} (conf: {result['confidence']:.2f})")
        return result

    # Fallback to PaddleOCR
    try:
        from ocr.plate_reader import _ocr_crop
        paddle_results = _ocr_crop(plate_crop)
        if paddle_results:
            best = max(paddle_results, key=lambda r: r.confidence)
            return {
                "text": best.text,
                "confidence": best.confidence,
                "source": "paddleocr",
            }
    except Exception as e:
        logger.debug(f"PaddleOCR fallback failed: {e}")

    return None
