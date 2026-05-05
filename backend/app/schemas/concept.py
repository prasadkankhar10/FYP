"""
schemas/concept.py — Pydantic schemas for Concept endpoints.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ConceptCreate(BaseModel):
    subject_id: int
    title: str
    content: Optional[str] = None
    difficulty: Optional[str] = "medium"  # easy | medium | hard
    parent_concept_id: Optional[int] = None  # Links to parent concept in knowledge graph


class ConceptUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    difficulty: Optional[str] = None


class ConceptOut(BaseModel):
    id: int
    subject_id: int
    user_id: int
    title: str
    content: Optional[str]
    difficulty: str
    created_at: datetime
    next_review_date: Optional[datetime] = None
    algorithm: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Quiz Question Schemas ──────────────────────────────────────────────────────

class QuizQuestionCreate(BaseModel):
    question_text: str
    question_type: str = "mcq"       # mcq | recall | truefalse
    options: Optional[str] = None    # JSON string: '["A","B","C","D"]'
    correct_answer: str
    difficulty_level: int = 3        # 1-5


class QuizQuestionOut(BaseModel):
    id: int
    concept_id: int
    question_text: str
    question_type: str
    options: Optional[str]
    correct_answer: str
    difficulty_level: int

    model_config = {"from_attributes": True}
