"""
Flipkart Gridlock — Violation Logic Engine
Rule-based violation detection using spatial geometry on YOLO detections.
No ML training needed — pure geometry + heuristics.
"""
from __future__ import annotations

import logging
from typing import List, Optional

import numpy as np

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models.schemas import (
    Detection, Violation, ViolationType, BBox, ZoneConfig
)
from config import (
    HELMET_HEAD_RATIO,
    HELMET_PROXIMITY_IOU,
    TRIPLE_RIDING_OVERLAP_THRESHOLD,
    SEATBELT_TORSO_TOP,
    SEATBELT_TORSO_BOTTOM,
    MIN_VIOLATION_CONFIDENCE,
    ZONE_VIOLATION_CONFIDENCE,
)

logger = logging.getLogger(__name__)


def detect_all_violations(
    detections: List[Detection],
    zones: Optional[List[ZoneConfig]] = None,
    image: Optional[np.ndarray] = None,
) -> List[Violation]:
    """
    Run all violation checks on a set of detections.

    Args:
        detections: List of detected objects from YOLO
        zones: Optional violation zones for zone-based checks
        image: Optional original image for pixel-level analysis

    Returns:
        List of detected violations
    """
    violations = []

    # Split detections by class
    persons = [d for d in detections if d.class_name == "person"]
    motorcycles = [d for d in detections if d.class_name == "motorcycle"]
    bicycles = [d for d in detections if d.class_name == "bicycle"]
    cars = [d for d in detections if d.class_name == "car"]
    buses = [d for d in detections if d.class_name == "bus"]
    trucks = [d for d in detections if d.class_name == "truck"]
    all_vehicles = cars + buses + trucks + motorcycles

    # ─── 1. Helmet Non-Compliance ────────────────────────────
    helmet_violations = check_helmet_compliance(persons, motorcycles, image)
    violations.extend(helmet_violations)

    # ─── 2. Triple Riding ────────────────────────────────────
    triple_violations = check_triple_riding(persons, motorcycles)
    violations.extend(triple_violations)

    # ─── 3. Seatbelt Non-Compliance ──────────────────────────
    seatbelt_violations = check_seatbelt_compliance(persons, cars, motorcycles, image)
    violations.extend(seatbelt_violations)

    # ─── 4. Zone-Based Violations ────────────────────────────
    if zones:
        zone_violations = check_zone_violations(all_vehicles, zones)
        violations.extend(zone_violations)

    # Filter by minimum confidence
    violations = [v for v in violations if v.confidence >= MIN_VIOLATION_CONFIDENCE]

    logger.info(f"Detected {len(violations)} violations from {len(detections)} detections")
    return violations


def check_helmet_compliance(
    persons: List[Detection],
    motorcycles: List[Detection],
    image: Optional[np.ndarray] = None,
) -> List[Violation]:
    """
    Detect helmet non-compliance.

    Logic:
    - Find persons that are near/on a motorcycle (proximity check)
    - For each rider, check if there's a helmet-like region in the head area
    - A rider without a detected head covering = violation

    Since YOLO COCO doesn't detect helmets, we use the heuristic that
    a rider on a motorcycle without protective headgear visible in the
    top portion of their bounding box indicates a violation.
    """
    violations = []

    for motorcycle in motorcycles:
        riders = _find_riders(persons, motorcycle)

        if not riders:
            continue

        for rider in riders:
            # Check head region of the rider
            head_region = _get_head_region(rider.bbox)

            # Heuristic: if person bbox is on motorcycle and the ratio
            # of person height to motorcycle height suggests they're riding
            # (not just standing nearby), flag as potential violation
            rider_on_bike = _is_rider_on_vehicle(rider, motorcycle)

            if rider_on_bike:
                # Check if they are missing a helmet using OpenCV skin detection
                is_missing_helmet = True
                if image is not None:
                    is_missing_helmet = _check_helmet_missing_hsv(head_region, image)

                if is_missing_helmet:
                    # Calculate confidence based on detection scores and proximity
                    confidence = min(rider.confidence, motorcycle.confidence) * 0.85

                    violations.append(Violation(
                        type=ViolationType.HELMET_MISSING,
                        confidence=round(confidence, 3),
                        description=f"Rider detected on motorcycle without visible helmet. "
                                    f"Rider confidence: {rider.confidence:.0%}",
                        detections=[rider, motorcycle],
                    ))

    return violations


def check_triple_riding(
    persons: List[Detection],
    motorcycles: List[Detection],
) -> List[Violation]:
    """
    Detect triple riding (3+ persons on one two-wheeler).

    Logic:
    - For each motorcycle, count persons whose bounding boxes
      significantly overlap with the motorcycle
    - If 3+ persons are associated with one motorcycle → violation
    """
    violations = []

    for motorcycle in motorcycles:
        riders = _find_riders(persons, motorcycle)

        if len(riders) >= 3:
            avg_confidence = np.mean(
                [r.confidence for r in riders] + [motorcycle.confidence]
            )

            violations.append(Violation(
                type=ViolationType.TRIPLE_RIDING,
                confidence=round(float(avg_confidence) * 0.9, 3),
                description=f"{len(riders)} persons detected on one motorcycle. "
                            f"Riders: {len(riders)}",
                detections=riders + [motorcycle],
            ))

    return violations


def check_seatbelt_compliance(
    persons: List[Detection],
    cars: List[Detection],
    motorcycles: List[Detection],
    image: Optional[np.ndarray] = None,
) -> List[Violation]:
    """
    Detect seatbelt non-compliance.

    Logic:
    - Find persons inside car bounding boxes (driver/passenger)
    - Exclude persons who are already riding motorcycles!
    - Check if a diagonal band pattern exists in the torso region
    - If no seatbelt pattern is detected → violation
    """
    violations = []

    # First, identify all persons on motorcycles so we don't check them for seatbelts
    bike_riders = set()
    for moto in motorcycles:
        riders = _find_riders(persons, moto)
        for r in riders:
            bike_riders.add(id(r))

    for car in cars:
        occupants = _find_occupants(persons, car)

        for occupant in occupants:
            # Skip if this person is actually on a motorcycle that happens to overlap with a car
            if id(occupant) in bike_riders:
                continue
            # Simple heuristic: if person is visible inside car,
            # and we can see their torso, flag as potential violation
            confidence = min(occupant.confidence, car.confidence) * 0.70

            if image is not None:
                # Try edge detection on torso region for seatbelt band
                has_belt = _check_seatbelt_edges(occupant.bbox, image)
                if has_belt:
                    continue  # Skip — seatbelt likely present

            violations.append(Violation(
                type=ViolationType.SEATBELT_MISSING,
                confidence=round(confidence, 3),
                description=f"Vehicle occupant detected without visible seatbelt. "
                            f"Person confidence: {occupant.confidence:.0%}",
                detections=[occupant, car],
            ))

    return violations


def check_zone_violations(
    vehicles: List[Detection],
    zones: List[ZoneConfig],
) -> List[Violation]:
    """
    Detect zone-based violations (stop line, wrong side, no parking).

    Logic:
    - For each active zone, check if any vehicle's center point
      falls inside the zone polygon
    - Map zone type to violation type
    """
    violations = []

    zone_type_map = {
        "stop_line": ViolationType.STOP_LINE,
        "wrong_side": ViolationType.WRONG_SIDE,
        "no_parking": ViolationType.ILLEGAL_PARKING,
        "red_light": ViolationType.RED_LIGHT,
    }

    for zone in zones:
        if not zone.active:
            continue

        violation_type = zone_type_map.get(zone.zone_type)
        if violation_type is None:
            continue

        polygon = np.array(zone.polygon, dtype=np.int32)

        for vehicle in vehicles:
            cx, cy = vehicle.bbox.center

            if _point_in_polygon(cx, cy, polygon):
                violations.append(Violation(
                    type=violation_type,
                    confidence=round(vehicle.confidence * ZONE_VIOLATION_CONFIDENCE, 3),
                    description=f"{vehicle.class_name} detected in {zone.name} zone. "
                                f"Zone type: {zone.zone_type}",
                    detections=[vehicle],
                    zone_id=zone.id,
                ))

    return violations


# ─── Helper Functions ────────────────────────────────────────

def _find_riders(persons: List[Detection], motorcycle: Detection) -> List[Detection]:
    """Find persons that are riding a given motorcycle."""
    riders = []
    for person in persons:
        # Check overlap between person and motorcycle
        overlap = motorcycle.bbox.overlap_ratio(person.bbox)
        iou = person.bbox.iou(motorcycle.bbox)

        # Person should be above or overlapping motorcycle
        person_bottom = person.bbox.y2
        moto_top = motorcycle.bbox.y1
        moto_bottom = motorcycle.bbox.y2

        is_near = (
            iou > HELMET_PROXIMITY_IOU or
            overlap > TRIPLE_RIDING_OVERLAP_THRESHOLD or
            (abs(person_bottom - moto_bottom) < motorcycle.bbox.height * 0.5 and
             _horizontal_overlap(person.bbox, motorcycle.bbox) > 0.3)
        )

        if is_near:
            riders.append(person)

    return riders


def _find_occupants(persons: List[Detection], car: Detection) -> List[Detection]:
    """Find persons inside a car bounding box."""
    occupants = []
    for person in persons:
        cx, cy = person.bbox.center
        if car.bbox.contains_point(cx, cy):
            occupants.append(person)
        elif person.bbox.iou(car.bbox) > 0.3:
            occupants.append(person)
    return occupants


def _is_rider_on_vehicle(person: Detection, vehicle: Detection) -> bool:
    """Determine if a person is actually riding (not just nearby)."""
    # Person's bottom should be near motorcycle's bottom (sitting)
    person_bottom = person.bbox.y2
    vehicle_bottom = vehicle.bbox.y2
    vehicle_height = vehicle.bbox.height

    bottom_proximity = abs(person_bottom - vehicle_bottom) < vehicle_height * 0.4

    # Person should be above vehicle center
    person_center_y = person.bbox.center[1]
    vehicle_center_y = vehicle.bbox.center[1]
    person_above = person_center_y <= vehicle_center_y + vehicle_height * 0.2

    # Horizontal alignment
    h_overlap = _horizontal_overlap(person.bbox, vehicle.bbox)

    return bottom_proximity and person_above and h_overlap > 0.2


def _get_head_region(bbox: BBox) -> BBox:
    """Extract the head region (top portion) of a person bbox."""
    head_height = int(bbox.height * HELMET_HEAD_RATIO)
    return BBox(
        x1=bbox.x1,
        y1=bbox.y1,
        x2=bbox.x2,
        y2=bbox.y1 + head_height,
    )


def _horizontal_overlap(a: BBox, b: BBox) -> float:
    """Calculate horizontal overlap ratio between two bboxes."""
    overlap_start = max(a.x1, b.x1)
    overlap_end = min(a.x2, b.x2)
    overlap_width = max(0, overlap_end - overlap_start)
    min_width = min(a.width, b.width)
    return overlap_width / min_width if min_width > 0 else 0.0


def _check_seatbelt_edges(bbox: BBox, image: np.ndarray) -> bool:
    """
    Simple edge-based seatbelt detection.
    Look for diagonal line patterns in the torso region.
    """
    try:
        import cv2

        # Extract torso region
        torso_y1 = bbox.y1 + int(bbox.height * SEATBELT_TORSO_TOP)
        torso_y2 = bbox.y1 + int(bbox.height * SEATBELT_TORSO_BOTTOM)
        torso = image[torso_y1:torso_y2, bbox.x1:bbox.x2]

        if torso.size == 0:
            return False

        # Convert to grayscale and detect edges
        gray = cv2.cvtColor(torso, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        # Look for diagonal lines using Hough transform
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=20,
                                 minLineLength=int(min(torso.shape[:2]) * 0.3),
                                 maxLineGap=5)

        if lines is None:
            return False

        # Check if any line has a diagonal angle (30-60 degrees)
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 - x1 == 0:
                continue
            angle = abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
            if 25 <= angle <= 65:
                return True

        return False
    except Exception:
        return False


def _check_helmet_missing_hsv(bbox: BBox, image: np.ndarray) -> bool:
    """
    Heuristic: Check the head region for skin tones.
    If a large portion of the head is skin-colored (face visible), 
    they likely are NOT wearing a full-face helmet.
    """
    try:
        import cv2

        head_crop = image[bbox.y1:bbox.y2, bbox.x1:bbox.x2]
        if head_crop.size == 0:
            return True

        # Convert to HSV color space
        hsv = cv2.cvtColor(head_crop, cv2.COLOR_BGR2HSV)

        # Define range for skin color in HSV
        lower_skin = np.array([0, 20, 70], dtype=np.uint8)
        upper_skin = np.array([20, 255, 255], dtype=np.uint8)

        # Threshold the HSV image to get only skin colors
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        
        # Calculate percentage of skin pixels
        skin_pixels = cv2.countNonZero(mask)
        total_pixels = mask.size
        skin_ratio = skin_pixels / total_pixels if total_pixels > 0 else 0

        # If more than 15% of the head region is skin, assume no helmet
        return skin_ratio > 0.15
    except Exception:
        return True


def _point_in_polygon(x: int, y: int, polygon: np.ndarray) -> bool:
    """Ray-casting algorithm for point-in-polygon test."""
    n = len(polygon)
    inside = False

    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]

        if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
            inside = not inside
        j = i

    return inside
