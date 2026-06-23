"""
AI Traffic Inspector — Zone Manager
Manages violation detection zones (stop lines, wrong-side boundaries, no-parking areas).
Supports interactive zone creation from the frontend.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemas.api_schemas import ZoneConfig

logger = logging.getLogger(__name__)

# In-memory zone storage (persisted to JSON file)
_zones: Dict[str, ZoneConfig] = {}
_zones_file: Optional[Path] = None


def init_zones(storage_path: Path = None):
    """Initialize zone manager, loading any saved zones."""
    global _zones_file
    if storage_path is None:
        storage_path = Path(__file__).resolve().parent.parent / "output" / "zones.json"
    _zones_file = storage_path

    if _zones_file.exists():
        try:
            with open(_zones_file) as f:
                data = json.load(f)
            for zone_data in data:
                zone = ZoneConfig(**zone_data)
                _zones[zone.id] = zone
            logger.info(f"Loaded {len(_zones)} zones from {_zones_file}")
        except Exception as e:
            logger.warning(f"Failed to load zones: {e}")

    # Add default demo zones if none exist
    if not _zones:
        _add_demo_zones()


def _add_demo_zones():
    """Add default demo zones for sample images."""
    demo_zones = [
        ZoneConfig(
            id="demo_stop_line_1",
            name="Stop Line - Main Junction",
            zone_type="stop_line",
            polygon=[(100, 400), (540, 400), (540, 440), (100, 440)],
            active=True,
        ),
        ZoneConfig(
            id="demo_wrong_side_1",
            name="Wrong Side - Left Lane",
            zone_type="wrong_side",
            polygon=[(0, 200), (200, 200), (200, 480), (0, 480)],
            active=True,
        ),
        ZoneConfig(
            id="demo_no_parking_1",
            name="No Parking Zone - Curb",
            zone_type="no_parking",
            polygon=[(400, 300), (640, 300), (640, 480), (400, 480)],
            active=True,
        ),
    ]

    for zone in demo_zones:
        _zones[zone.id] = zone

    _save_zones()
    logger.info(f"Added {len(demo_zones)} demo zones")


def _save_zones():
    """Persist zones to JSON file."""
    if _zones_file is None:
        return
    try:
        _zones_file.parent.mkdir(parents=True, exist_ok=True)
        data = [zone.model_dump() for zone in _zones.values()]
        with open(_zones_file, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save zones: {e}")


def add_zone(zone: ZoneConfig) -> ZoneConfig:
    """Add a new violation zone."""
    _zones[zone.id] = zone
    _save_zones()
    logger.info(f"Added zone: {zone.name} ({zone.zone_type})")
    return zone


def update_zone(zone_id: str, updates: dict) -> Optional[ZoneConfig]:
    """Update an existing zone."""
    if zone_id not in _zones:
        return None
    zone_data = _zones[zone_id].model_dump()
    zone_data.update(updates)
    _zones[zone_id] = ZoneConfig(**zone_data)
    _save_zones()
    return _zones[zone_id]


def delete_zone(zone_id: str) -> bool:
    """Delete a zone by ID."""
    if zone_id in _zones:
        del _zones[zone_id]
        _save_zones()
        return True
    return False


def get_zone(zone_id: str) -> Optional[ZoneConfig]:
    """Get a single zone by ID."""
    return _zones.get(zone_id)


def get_all_zones() -> List[ZoneConfig]:
    """Get all zones."""
    return list(_zones.values())


def get_active_zones() -> List[ZoneConfig]:
    """Get only active zones."""
    return [z for z in _zones.values() if z.active]


def clear_zones():
    """Remove all zones."""
    _zones.clear()
    _save_zones()


def draw_zones_on_image(image: np.ndarray, zones: List[ZoneConfig] = None) -> np.ndarray:
    """
    Draw zone overlays on an image for visualization.

    Args:
        image: BGR numpy array
        zones: Zones to draw (defaults to all active zones)

    Returns:
        Image with zone overlays drawn
    """
    import cv2

    if zones is None:
        zones = get_active_zones()

    overlay = image.copy()
    zone_colors = {
        "stop_line": (0, 0, 255),      # Red
        "wrong_side": (0, 165, 255),    # Orange
        "no_parking": (255, 0, 255),    # Magenta
        "red_light": (0, 0, 200),       # Dark Red
    }

    for zone in zones:
        color = zone_colors.get(zone.zone_type, (128, 128, 128))
        pts = np.array(zone.polygon, dtype=np.int32)

        # Semi-transparent fill
        cv2.fillPoly(overlay, [pts], color)

        # Border
        cv2.polylines(image, [pts], isClosed=True, color=color, thickness=2)

        # Label
        centroid = pts.mean(axis=0).astype(int)
        cv2.putText(image, zone.name, tuple(centroid),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    # Blend overlay with original (40% transparency)
    result = cv2.addWeighted(overlay, 0.3, image, 0.7, 0)
    return result
