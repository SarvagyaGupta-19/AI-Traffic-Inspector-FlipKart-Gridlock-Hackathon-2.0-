"""
Flipkart Gridlock — Demo Data Seeder
Seeds the database with realistic demo violations so the dashboard
looks populated for hackathon judging.
"""
from __future__ import annotations

import json
import logging
import random
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal, store_violation, ViolationDB

logger = logging.getLogger(__name__)

# Demo violation templates
DEMO_VIOLATIONS = [
    {
        "type": "helmet_missing",
        "descriptions": [
            "Motorcycle rider detected without helmet near MG Road junction",
            "Two-wheeler rider without protective headgear on NH-48",
            "Rider on motorcycle at Silk Board signal - no helmet detected",
            "Biker without helmet spotted near Electronic City toll",
            "Motorcycle rider at Koramangala 5th Block - helmet absent",
        ],
        "plates": ["KA01AB1234", "KA05MN7890", "KA03CD5678", "MH02XY9012", "TN09PQ3456"],
    },
    {
        "type": "seatbelt_missing",
        "descriptions": [
            "Car driver without seatbelt at Indiranagar signal",
            "Vehicle occupant - seatbelt not visible at Whitefield Road",
            "Driver in sedan at Marathahalli bridge - no seatbelt detected",
            "Car at Hebbal flyover - front passenger without seatbelt",
            "SUV driver at Yeshwantpur Circle - seatbelt not worn",
        ],
        "plates": ["KA01MX4567", "KA02HH8901", "DL03EF2345", "KA04GH6789", "AP05IJ0123"],
    },
    {
        "type": "triple_riding",
        "descriptions": [
            "Three persons detected on motorcycle near Majestic bus stand",
            "Triple riding on two-wheeler at BTM Layout junction",
            "3 riders on single motorcycle - Jayanagar 4th Block",
            "Triple riding violation near Banashankari bus stop",
            "Three occupants on motorcycle at Wilson Garden",
        ],
        "plates": ["KA01ZZ1111", "KA09BB2222", "KA51CC3333", "TN22DD4444", "KA03EE5555"],
    },
    {
        "type": "wrong_side",
        "descriptions": [
            "Vehicle driving on wrong side near Dairy Circle underpass",
            "Car travelling against traffic flow on Hosur Road",
            "Two-wheeler on wrong side at Madiwala junction",
            "Auto-rickshaw going wrong way on Outer Ring Road",
            "Vehicle entering one-way road at Richmond Circle",
        ],
        "plates": ["KA01FF6666", "KA05GG7777", "MH01HH8888", "KA02II9999", "KA04JJ0000"],
    },
    {
        "type": "stop_line",
        "descriptions": [
            "Vehicle crossed stop line at red signal — Residency Road",
            "Car past stop line at Shivajinagar traffic light",
            "Motorcycle beyond stop line at Ulsoor Lake junction",
            "SUV crossed stop line at Brigade Road signal",
            "Bus past stop line at Mahatma Gandhi Road signal",
        ],
        "plates": ["KA01KK1122", "KA03LL3344", "KA05MM5566", "TN10NN7788", "KA01OO9900"],
    },
]


def seed_demo_data(count: int = 30):
    """
    Seed the database with demo violations.

    Args:
        count: Number of demo violations to create
    """
    db = SessionLocal()

    try:
        # Check if data already exists
        existing = db.query(ViolationDB).count()
        if existing > 0:
            logger.info(f"Database already has {existing} records. Skipping seed.")
            return

        logger.info(f"Seeding {count} demo violations...")

        for i in range(count):
            template = random.choice(DEMO_VIOLATIONS)
            description = random.choice(template["descriptions"])
            plate = random.choice(template["plates"])

            # Random timestamp in the last 7 days
            days_ago = random.uniform(0, 7)
            hours_ago = random.uniform(0, 24)
            timestamp = datetime.now() - timedelta(
                days=days_ago, hours=hours_ago
            )

            # Random confidence between 0.55 and 0.95
            confidence = round(random.uniform(0.55, 0.95), 3)

            # Decide plate presence once so plate_text and plate_confidence are consistent
            has_plate = random.random() > 0.3  # 70% have plates

            store_violation(
                db=db,
                violation_type=template["type"],
                confidence=confidence,
                description=description,
                plate_text=plate if has_plate else None,
                plate_confidence=round(random.uniform(0.6, 0.95), 3) if has_plate else None,
                image_path="",  # Demo records have no real image files
                evidence_path="",  # Demo records have no real evidence files
                timestamp=timestamp,
            )

        logger.info(f"✓ Seeded {count} demo violations successfully")

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    from app.database import init_db
    init_db()
    seed_demo_data()
    print("Demo data seeded successfully!")
