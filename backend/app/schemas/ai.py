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
    parent_concept: Optional[str] = None

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
    follow_up_question: Optional[str] = None

class BridgeSuggestion(BaseModel):
    title: str
    content: str
    source_concept_id: int
    target_concept_id: int
    rationale: str

class SuggestBridgesResponse(BaseModel):
    suggestions: List[BridgeSuggestion]


class ExamRecapResponse(BaseModel):
    recap_markdown: str
