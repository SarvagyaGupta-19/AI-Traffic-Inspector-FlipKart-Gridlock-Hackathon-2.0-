"""
AI Traffic Inspector — Central Configuration
All configurable parameters in one place.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ─── Base Paths ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"
SAMPLES_DIR = DATA_DIR / "samples"
OUTPUT_DIR = BASE_DIR / "output"
UPLOADS_DIR = OUTPUT_DIR / "uploads"
EVIDENCE_DIR = OUTPUT_DIR / "evidence"
MODELS_DIR = BASE_DIR / "weights"

# Create directories on import
for d in [DATA_DIR, SAMPLES_DIR, OUTPUT_DIR, UPLOADS_DIR, EVIDENCE_DIR, MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Database ────────────────────────────────────────────────
DATABASE_URL = f"sqlite:///{OUTPUT_DIR / 'gridlock.db'}"

# ─── YOLO Model ──────────────────────────────────────────────
YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8s.pt")  # Pretrained small model
YOLO_CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", "0.35"))
YOLO_IOU_THRESHOLD = float(os.getenv("YOLO_IOU", "0.45"))
YOLO_IMG_SIZE = int(os.getenv("YOLO_IMG_SIZE", "640"))

# COCO classes relevant to traffic
TRAFFIC_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    9: "traffic light",
    11: "stop sign",
}

# ─── Violation Thresholds ────────────────────────────────────
# Helmet detection: ratio of person bbox top region to check
HELMET_HEAD_RATIO = 0.30  # Top 30% of person bbox is "head region"
HELMET_PROXIMITY_IOU = 0.10  # Min IoU between person and motorcycle

# Triple riding: max distance for person clustering on motorcycle
TRIPLE_RIDING_OVERLAP_THRESHOLD = 0.15

# Seatbelt: torso region of person inside car
SEATBELT_TORSO_TOP = 0.25  # 25-65% of person bbox height
SEATBELT_TORSO_BOTTOM = 0.65

# Zone violations: default confidence for zone-based violations
ZONE_VIOLATION_CONFIDENCE = 0.80

# Minimum confidence to report a violation
MIN_VIOLATION_CONFIDENCE = 0.40

# ─── OCR ─────────────────────────────────────────────────────
OCR_LANG = "en"
OCR_USE_ANGLE_CLS = False  # Faster performance for real-time
FAST_OCR_MODE = True       # Skip full-image OCR on video frames
# Indian plate regex: 2 letters + 2 digits + 1-3 letters + 4 digits
INDIAN_PLATE_REGEX = r"^[A-Z]{2}\s?\d{1,2}\s?[A-Z]{1,3}\s?\d{4}$"
OCR_MIN_CONFIDENCE = 0.50

# ─── Evidence Annotation ─────────────────────────────────────
EVIDENCE_FONT_SIZE = 16
EVIDENCE_BOX_COLORS = {
    "violation": (255, 69, 58),     # Red
    "compliant": (52, 199, 89),     # Green
    "plate": (0, 122, 255),         # Blue
    "detection": (255, 214, 10),    # Yellow
}
EVIDENCE_WATERMARK = "AI TRAFFIC INSPECTOR EVIDENCE"

# ─── Server ──────────────────────────────────────────────────
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
CORS_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://*.vercel.app",
    "*",  # Allow all for hackathon demo
]

# ─── Video Streaming ─────────────────────────────────────────
STREAM_FRAME_INTERVAL = 0.1  # seconds between frame processing
MAX_STREAM_FPS = 10  # Max frames per second for WebSocket streaming
VIDEO_FRAME_WIDTH = 640  # Resize frames for processing

# ─── Cascade Pipeline (Multi-Stage) ─────────────────────────
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")
if not ROBOFLOW_API_KEY:
    raise ValueError("ROBOFLOW_API_KEY environment variable is not set")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

# Roboflow hosted model IDs
RF_VEHICLE_MODEL = "vehicle-detection-bz0yu/4"
RF_PEOPLE_MODEL = "people-detection-o4rdr/7"
RF_PLATE_MODEL = "license-plate-recognition-rxg4e/4"

# Use ByteTrack for video streams
USE_BYTETRACK = True
