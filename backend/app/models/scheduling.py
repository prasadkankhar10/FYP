"""
models/scheduling.py — SchedulingData ORM model.
One row per (user, concept, algorithm) triple.
Stores both SM-2 and FSRS state so users can switch algorithms.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class SchedulingData(Base):
    __tablename__ = "scheduling_data"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Which algorithm is currently active for this card
    algorithm = Column(String(20), default="sm2")  # sm2 | fsrs | multi_fsrs

    # ── SM-2 Fields ──────────────────────────────────────────────────────────
    ease_factor = Column(Float, default=2.5)    # EF: starts at 2.5
    interval_days = Column(Integer, default=1)  # Days until next review
    repetitions = Column(Integer, default=0)    # Number of successful reviews

    # ── FSRS Fields ──────────────────────────────────────────────────────────
    stability = Column(Float, default=0.0)      # S: how stable the memory is
    difficulty_fsrs = Column(Float, default=5.0)  # D: inherent difficulty (1-10)
    retrievability = Column(Float, default=1.0) # R: current recall probability

    # ── Scheduling ────────────────────────────────────────────────────────────
    next_review_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_review_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    concept = relationship("Concept", back_populates="scheduling_data")
    user = relationship("User", back_populates="scheduling_data")
