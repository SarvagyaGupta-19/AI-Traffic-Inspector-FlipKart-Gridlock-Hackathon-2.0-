"""
AI Traffic Inspector — Data Schemas
Pydantic models that define the output contract for the entire pipeline.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field


class ViolationType(str, Enum):
    """Supported violation types for MVP."""
    HELMET_MISSING = "helmet_missing"
    SEATBELT_MISSING = "seatbelt_missing"
    TRIPLE_RIDING = "triple_riding"
    WRONG_SIDE = "wrong_side"
    STOP_LINE = "stop_line"
    RED_LIGHT = "red_light"
    ILLEGAL_PARKING = "illegal_parking"


class BBox(BaseModel):
    """Bounding box coordinates (pixel space)."""
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        return self.y2 - self.y1

    @property
    def center(self) -> Tuple[int, int]:
        return ((self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2)

    @property
    def area(self) -> int:
        return self.width * self.height

    def iou(self, other: BBox) -> float:
        """Calculate Intersection over Union with another bbox."""
        xi1 = max(self.x1, other.x1)
        yi1 = max(self.y1, other.y1)
        xi2 = min(self.x2, other.x2)
        yi2 = min(self.y2, other.y2)
        inter = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        union = self.area + other.area - inter
        return inter / union if union > 0 else 0.0

    def contains_point(self, x: int, y: int) -> bool:
        """Check if a point is inside this bbox."""
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def overlap_ratio(self, other: BBox) -> float:
        """What fraction of 'other' overlaps with this bbox."""
        xi1 = max(self.x1, other.x1)
        yi1 = max(self.y1, other.y1)
        xi2 = min(self.x2, other.x2)
        yi2 = min(self.y2, other.y2)
        inter = max(0, xi2 - xi1) * max(0, yi2 - yi1)
        return inter / other.area if other.area > 0 else 0.0


class Detection(BaseModel):
    """A single detected object from YOLO."""
    bbox: BBox
    class_name: str
    class_id: int
    confidence: float = Field(ge=0.0, le=1.0)
    track_id: Optional[int] = None  # For video tracking


class PlateResult(BaseModel):
    """License plate OCR result."""
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: BBox
    raw_text: str = ""  # Before regex cleanup


class Violation(BaseModel):
    """A detected traffic violation."""
    id: Optional[int] = None
    type: ViolationType
    confidence: float = Field(ge=0.0, le=1.0)
    description: str = ""
    detections: List[Detection] = []
    plate: Optional[PlateResult] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    evidence_path: Optional[str] = None
    image_path: Optional[str] = None
    zone_id: Optional[str] = None  # For zone-based violations


class AnalysisResult(BaseModel):
    """Complete analysis result for a single image/frame."""
    image_path: str
    detections: List[Detection] = []
    violations: List[Violation] = []
    plates: List[PlateResult] = []
    processing_time_ms: float = 0.0
    frame_number: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# ─── API Request/Response Models ─────────────────────────────

class UploadResponse(BaseModel):
    """Response for image upload endpoint."""
    success: bool
    message: str
    result: Optional[AnalysisResult] = None
    violations_count: int = 0


class ViolationRecord(BaseModel):
    """Stored violation record from database."""
    id: int
    type: str
    confidence: float
    description: str
    plate_text: Optional[str]
    plate_confidence: Optional[float]
    timestamp: str
    image_path: str
    evidence_path: Optional[str]
    detections_json: Optional[str]


class ViolationListResponse(BaseModel):
    """Paginated violation list response."""
    violations: List[ViolationRecord]
    total: int
    page: int
    per_page: int


class AnalyticsResponse(BaseModel):
    """Analytics summary response."""
    total_violations: int
    by_type: dict  # {violation_type: count}
    by_day: dict  # {date_str: count}
    recent: List[ViolationRecord]
    avg_confidence: float
    plates_detected: int


class ZoneConfig(BaseModel):
    """Configuration for a violation detection zone."""
    id: str
    name: str
    zone_type: str  # "stop_line", "wrong_side", "no_parking"
    polygon: List[Tuple[int, int]]  # List of (x, y) vertices
    active: bool = True


class StreamConfig(BaseModel):
    """Configuration for video stream processing."""
    source: str  # URL or file path
    zones: List[ZoneConfig] = []
    detect_violations: List[ViolationType] = [
        ViolationType.HELMET_MISSING,
        ViolationType.TRIPLE_RIDING,
    ]
    frame_skip: int = 2  # Process every Nth frame
