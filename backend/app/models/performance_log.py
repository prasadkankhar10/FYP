"""
models/performance_log.py — PerformanceLog ORM model.
Aggregated performance snapshots per (user, concept) over a time window.
Used for analytics charts and algorithm comparison reports.
"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class PerformanceLog(Base):
    __tablename__ = "performance_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)

    accuracy_percent = Column(Float, default=0.0)     # correct / total * 100
    avg_response_time = Column(Float, default=0.0)    # Average seconds per answer
    total_reviews = Column(Integer, default=0)
    correct_reviews = Column(Integer, default=0)
    stability_growth = Column(Float, default=0.0)     # FSRS: S increase over period

    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="performance_logs")
    concept = relationship("Concept", back_populates="performance_logs")
