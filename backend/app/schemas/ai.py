"""
schemas/ai.py — Pydantic schemas for AI endpoints
"""
from pydantic import BaseModel
from typing import Optional, List

class AIAdviceResponse(BaseModel):
    advice_markdown: str

class AutoFlashcardRequest(BaseModel):
    subject_id: int
    source_text: str

class FlashcardItem(BaseModel):
    title: str
    content: str

class AutoFlashcardResponse(BaseModel):
    message: str
    cards: List[FlashcardItem]

class SaveFlashcardsRequest(BaseModel):
    subject_id: int
    cards: List[FlashcardItem]

class SaveFlashcardsResponse(BaseModel):
    message: str
    concepts_created: int

class ConnectConceptsResponse(BaseModel):
    message: str
    connections_made: int

class AIEvaluateRequest(BaseModel):
    concept_id: int
    typed_answer: str

class AIEvaluateResponse(BaseModel):
    sm2_score: int
    fsrs_score: int
    feedback_markdown: str
    confidence_score: float = 1.0
