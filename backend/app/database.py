"""
Flipkart Gridlock — Database Layer
SQLAlchemy + SQLite for violation record storage.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text, DateTime,
    Boolean, desc, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATABASE_URL

logger = logging.getLogger(__name__)

# ─── SQLAlchemy Setup ────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
    echo=False,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ─── Models ──────────────────────────────────────────────────

class ViolationDB(Base):
    """Violation record in the database."""
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    description = Column(Text, default="")
    plate_text = Column(String(20), default=None, index=True)
    plate_confidence = Column(Float, default=None)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    image_path = Column(String(500), default="")
    evidence_path = Column(String(500), default="")
    detections_json = Column(Text, default="[]")
    metadata_json = Column(Text, default="{}")
    zone_id = Column(String(100), default=None)
    frame_number = Column(Integer, default=None)
    location = Column(String(255), default=None)
    status = Column(String(20), default="pending", index=True) # pending, issued, rejected
    created_at = Column(DateTime, default=datetime.utcnow)


class UserDB(Base):
    """Admin user for the dashboard."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# ─── Database Initialization ────────────────────────────────

def init_db():
    """Create all tables and seed default admin."""
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        admin_user = db.query(UserDB).filter(UserDB.username == "admin").first()
        if not admin_user:
            admin_user = UserDB(
                username="admin",
                hashed_password=pwd_context.hash("admin")
            )
            db.add(admin_user)
            db.commit()
            logger.info("Created default admin user (admin:admin)")
    finally:
        db.close()
    
    logger.info("Database initialized")


def get_db():
    """Dependency for FastAPI route injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── CRUD Operations ────────────────────────────────────────

def store_violation(
    db: Session,
    violation_type: str,
    confidence: float,
    description: str = "",
    plate_text: Optional[str] = None,
    plate_confidence: Optional[float] = None,
    image_path: str = "",
    evidence_path: str = "",
    detections: list = None,
    zone_id: Optional[str] = None,
    frame_number: Optional[int] = None,
    location: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> ViolationDB:
    """Store a new violation record."""
    record = ViolationDB(
        type=violation_type,
        confidence=confidence,
        description=description,
        plate_text=plate_text,
        plate_confidence=plate_confidence,
        image_path=image_path,
        evidence_path=evidence_path,
        detections_json=json.dumps([d.model_dump() if hasattr(d, 'model_dump') else d
                                      for d in (detections or [])]),
        zone_id=zone_id,
        frame_number=frame_number,
        location=location,
        status="pending",
        timestamp=timestamp or datetime.utcnow(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    logger.info(f"Stored violation #{record.id}: {violation_type}")
    return record


def get_violations(
    db: Session,
    page: int = 1,
    per_page: int = 20,
    violation_type: Optional[str] = None,
    plate: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> tuple[List[ViolationDB], int]:
    """Get paginated violations with optional filtering."""
    query = db.query(ViolationDB)

    if violation_type:
        query = query.filter(ViolationDB.type == violation_type)
    if plate:
        query = query.filter(ViolationDB.plate_text.ilike(f"%{plate}%"))
    if status:
        query = query.filter(ViolationDB.status == status)
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(ViolationDB.timestamp >= start_dt)
        except ValueError:
            pass  # Invalid date format, skip filter
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(ViolationDB.timestamp <= end_dt)
        except ValueError:
            pass  # Invalid date format, skip filter

    total = query.count()
    violations = query.order_by(desc(ViolationDB.timestamp)) \
                      .offset((page - 1) * per_page) \
                      .limit(per_page) \
                      .all()

    return violations, total


def get_violation_by_id(db: Session, violation_id: int) -> Optional[ViolationDB]:
    """Get a single violation by ID."""
    return db.query(ViolationDB).filter(ViolationDB.id == violation_id).first()


def delete_violation(db: Session, violation_id: int) -> bool:
    """Delete a violation record."""
    record = get_violation_by_id(db, violation_id)
    if record:
        db.delete(record)
        db.commit()
        return True
    return False


def get_analytics(db: Session) -> dict:
    """Get analytics summary."""
    total = db.query(func.count(ViolationDB.id)).scalar() or 0

    # By type
    type_counts = db.query(
        ViolationDB.type, func.count(ViolationDB.id)
    ).group_by(ViolationDB.type).all()
    by_type = {t: c for t, c in type_counts}

    # By day (last 30 days)
    day_counts = db.query(
        func.date(ViolationDB.timestamp),
        func.count(ViolationDB.id)
    ).group_by(func.date(ViolationDB.timestamp)) \
     .order_by(desc(func.date(ViolationDB.timestamp))) \
     .limit(30).all()
    by_day = {str(d): c for d, c in day_counts}

    # Recent violations
    recent = db.query(ViolationDB).order_by(
        desc(ViolationDB.timestamp)
    ).limit(10).all()

    # Average confidence
    avg_conf = db.query(func.avg(ViolationDB.confidence)).scalar() or 0.0

    # Plates detected
    plates = db.query(func.count(ViolationDB.id)).filter(
        ViolationDB.plate_text.isnot(None),
        ViolationDB.plate_text != "",
    ).scalar() or 0

    return {
        "total_violations": total,
        "by_type": by_type,
        "by_day": by_day,
        "recent": recent,
        "avg_confidence": round(float(avg_conf), 3),
        "plates_detected": plates,
    }


def clear_all_violations(db: Session) -> int:
    """Delete all violation records. Returns count of deleted rows."""
    count = db.query(ViolationDB).count()
    db.query(ViolationDB).delete()
    db.commit()
    logger.info(f"Cleared {count} violation records")
    return count

