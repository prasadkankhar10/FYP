"""
models/user.py — User ORM model.
Stores authentication info and personalized FSRS parameters.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # FSRS personalized weights stored as a JSON string
    # Default is None — uses global FSRS-4 initial parameters
    fsrs_params = Column(Text, nullable=True)

    # User's academic goals or profile for AI Customization
    bio = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    subjects = relationship("Subject", back_populates="user", cascade="all, delete-orphan")
    concepts = relationship("Concept", back_populates="user", cascade="all, delete-orphan")
    review_logs = relationship("ReviewLog", back_populates="user", cascade="all, delete-orphan")
    performance_logs = relationship("PerformanceLog", back_populates="user", cascade="all, delete-orphan")
    scheduling_data = relationship("SchedulingData", back_populates="user", cascade="all, delete-orphan")
