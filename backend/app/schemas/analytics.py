"""
schemas/analytics.py — Pydantic schemas for Analytics endpoints.
"""
from pydantic import BaseModel
from typing import List, Optional


class OverviewStats(BaseModel):
    total_concepts: int
    total_reviews: int
    overall_accuracy: float
    due_today: int
    current_streak: int  # consecutive days with reviews


class RetentionPoint(BaseModel):
    """A single point on the retention curve."""
    day: int
    retrievability: float
    concept_title: str


class AlgorithmCompareStats(BaseModel):
    algorithm: str
    total_reviews: int
    correct_reviews: int
    accuracy: float
    avg_interval_days: float
    avg_stability: Optional[float] = None  # FSRS only
    log_loss: Optional[float] = None
    rmse: Optional[float] = None


class StabilityPoint(BaseModel):
    concept_title: str
    review_number: int
    stability: float
