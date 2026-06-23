import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)

def preprocess_image(image: np.ndarray) -> np.ndarray:
    """
    Apply a series of image processing techniques to normalize and enhance
    surveillance images before they are passed to the detection models.
    
    This fulfills the Image Preprocessing Layer requirements:
    - Brightness normalization & Contrast enhancement (CLAHE)
    - Noise reduction (Gaussian)
    - Sharpening (Unsharp masking)
    """
    try:
        # 1. Convert to LAB color space to work on the Lightness channel
        # This prevents color distortion when enhancing contrast
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # 2. Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # This solves low light conditions, shadows, and overexposure from headlights
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)

        # 3. Merge the CLAHE enhanced L-channel back with A and B channels
        merged_lab = cv2.merge((cl, a_channel, b_channel))
        enhanced_bgr = cv2.cvtColor(merged_lab, cv2.COLOR_LAB2BGR)

        # 4. Noise Reduction (mild blur to remove grain/artifacts)
        # Useful for low-resolution surveillance cameras or rain/haze
        denoised = cv2.GaussianBlur(enhanced_bgr, (3, 3), 0)

        # 5. Sharpening (Unsharp masking)
        # Recovers edges lost during noise reduction, critical for License Plates
        gaussian = cv2.GaussianBlur(denoised, (9, 9), 10.0)
        sharpened = cv2.addWeighted(denoised, 1.5, gaussian, -0.5, 0)

        return sharpened
    except Exception as e:
        logger.error(f"Image preprocessing failed, returning original image: {e}")
        return image

def is_image_too_blurry(image: np.ndarray, threshold: float = 100.0) -> bool:
    """
    Detect if an image suffers from severe motion blur or focus issues.
    Calculates the variance of the Laplacian.
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    return variance < threshold
