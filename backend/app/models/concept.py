"""
models/concept.py — Concept ORM model.
A Concept is an individual learning item (e.g., "Pythagoras Theorem").
Each concept is independently tracked by the scheduling algorithm.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
import enum


class DifficultyLevel(str, enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class Concept(Base):
    __tablename__ = "concepts"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)         # Study notes / explanation
    difficulty = Column(String(10), default="medium")  # easy | medium | hard
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="concepts")
    subject = relationship("Subject", back_populates="concepts")
    parent = relationship("Concept", remote_side=[id], backref="children")
    scheduling_data = relationship("SchedulingData", back_populates="concept", cascade="all, delete-orphan")
    review_logs = relationship("ReviewLog", back_populates="concept", cascade="all, delete-orphan")
    quiz_questions = relationship("QuizQuestion", back_populates="concept", cascade="all, delete-orphan")
    performance_logs = relationship("PerformanceLog", back_populates="concept", cascade="all, delete-orphan")

    @property
    def next_review_date(self):
        if self.scheduling_data and len(self.scheduling_data) > 0:
            return self.scheduling_data[0].next_review_date
        return None

    @property
    def algorithm(self):
        if self.scheduling_data and len(self.scheduling_data) > 0:
            return self.scheduling_data[0].algorithm
        return None
