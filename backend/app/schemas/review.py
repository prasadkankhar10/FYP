"""
schemas/review.py — Pydantic schemas for Review and Scheduling endpoints.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ReviewSubmit(BaseModel):
    concept_id: int
    quality_score: int          # SM-2: 0-5 | FSRS: 1-4
    was_correct: bool
    response_time_sec: Optional[float] = None


class ReviewLogOut(BaseModel):
    id: int
    concept_id: int
    user_id: int
    algorithm_used: str
    quality_score: int
    was_correct: bool
    response_time_sec: Optional[float]
    retention_at_review: Optional[float]
    reviewed_at: datetime

    model_config = {"from_attributes": True}


class SchedulingDataOut(BaseModel):
    id: int
    concept_id: int
    algorithm: str
    ease_factor: float
    interval_days: int
    repetitions: int
    stability: float
    difficulty_fsrs: float
    retrievability: float
    next_review_date: datetime
    last_review_date: Optional[datetime]

    model_config = {"from_attributes": True}


class AlgorithmSwitch(BaseModel):
    algorithm: str   # sm2 | fsrs | multi_fsrs


class DueConceptOut(BaseModel):
    """A concept that is due for review today, with its scheduling data."""
    concept_id: int
    concept_title: str
    concept_content: Optional[str] = None
    subject_name: str
    algorithm: str
    next_review_date: datetime
    retrievability: float
    interval_days: int
    priority_score: Optional[float] = None  # Used by Multi-FSRS
