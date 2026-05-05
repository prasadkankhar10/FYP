"""
models/review_log.py — ReviewLog ORM model.
Append-only table: every review attempt creates one row.
This is the primary data source for analytics and algorithm comparison.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class ReviewLog(Base):
    __tablename__ = "review_logs"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    algorithm_used = Column(String(20), nullable=False)  # sm2 | fsrs | multi_fsrs

    # SM-2 quality score: 0-5
    # FSRS rating: 1=Again, 2=Hard, 3=Good, 4=Easy
    quality_score = Column(Integer, nullable=False)

    response_time_sec = Column(Float, nullable=True)   # Time taken to answer
    was_correct = Column(Boolean, nullable=False)       # Did user answer correctly?

    # Retrievability (R) value at the moment of review — key for FSRS analytics
    retention_at_review = Column(Float, nullable=True)

    reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    concept = relationship("Concept", back_populates="review_logs")
    user = relationship("User", back_populates="review_logs")
