"""
AI Traffic Inspector — Image Utilities
Helper functions for image loading, resizing, and format conversion.
"""
from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional, Tuple, Union

import cv2
import numpy as np


def load_image(path: Union[str, Path]) -> Optional[np.ndarray]:
    """Load an image from disk as BGR numpy array."""
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Could not load image: {path}")
    return img


def resize_image(
    image: np.ndarray,
    max_width: int = 1280,
    max_height: int = 720,
) -> np.ndarray:
    """Resize image to fit within max dimensions while preserving aspect ratio."""
    h, w = image.shape[:2]
    scale = min(max_width / w, max_height / h, 1.0)
    if scale < 1.0:
        new_w = int(w * scale)
        new_h = int(h * scale)
        return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return image


def image_to_base64(image: np.ndarray, format: str = "jpg", quality: int = 85) -> str:
    """Convert a numpy image to base64 string."""
    if format == "jpg":
        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, quality])
    else:
        _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer.tobytes()).decode('utf-8')


def base64_to_image(b64_string: str) -> np.ndarray:
    """Convert a base64 string to numpy image."""
    img_bytes = base64.b64decode(b64_string)
    nparr = np.frombuffer(img_bytes, np.uint8)
    return cv2.imdecode(nparr, cv2.IMREAD_COLOR)


def get_image_info(path: Union[str, Path]) -> dict:
    """Get basic image information."""
    img = load_image(path)
    h, w, c = img.shape
    file_size = Path(path).stat().st_size
    return {
        "width": w,
        "height": h,
        "channels": c,
        "file_size_kb": round(file_size / 1024, 1),
        "format": Path(path).suffix,
    }


def apply_augmentation(image: np.ndarray, augmentation_type: str = "random") -> np.ndarray:
    """
    Apply image augmentation for testing robustness.
    Simulates difficult conditions: low light, rain, blur, shadows.
    """
    if augmentation_type == "low_light":
        return _simulate_low_light(image)
    elif augmentation_type == "blur":
        return _simulate_blur(image)
    elif augmentation_type == "rain":
        return _simulate_rain(image)
    elif augmentation_type == "shadow":
        return _simulate_shadow(image)
    elif augmentation_type == "random":
        import random
        aug = random.choice(["low_light", "blur", "rain", "shadow"])
        return apply_augmentation(image, aug)
    return image


def _simulate_low_light(image: np.ndarray) -> np.ndarray:
    """Reduce brightness to simulate low-light conditions."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 2] *= 0.3  # Reduce value channel
    hsv = np.clip(hsv, 0, 255).astype(np.uint8)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def _simulate_blur(image: np.ndarray) -> np.ndarray:
    """Apply motion blur to simulate camera shake."""
    ksize = 15
    kernel = np.zeros((ksize, ksize))
    kernel[int((ksize - 1) / 2), :] = np.ones(ksize)
    kernel /= ksize
    return cv2.filter2D(image, -1, kernel)


def _simulate_rain(image: np.ndarray) -> np.ndarray:
    """Add rain-like streaks to the image."""
    h, w = image.shape[:2]
    rain = np.zeros_like(image)
    for _ in range(100):
        x = np.random.randint(0, w)
        y = np.random.randint(0, h)
        length = np.random.randint(10, 30)
        cv2.line(rain, (x, y), (x + 1, y + length), (200, 200, 200), 1)
    return cv2.addWeighted(image, 0.85, rain, 0.15, 0)


def _simulate_shadow(image: np.ndarray) -> np.ndarray:
    """Add a random shadow to the image."""
    h, w = image.shape[:2]
    shadow = image.copy()

    # Random polygon shadow
    pts = np.array([
        [np.random.randint(0, w), 0],
        [np.random.randint(0, w), h],
        [np.random.randint(0, w), h],
        [np.random.randint(0, w), 0],
    ], dtype=np.int32)

    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.fillPoly(mask, [pts], 255)

    shadow[mask > 0] = (shadow[mask > 0] * 0.5).astype(np.uint8)
    return shadow
