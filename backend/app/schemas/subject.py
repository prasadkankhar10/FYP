"""
schemas/subject.py — Pydantic schemas for Subject endpoints.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SubjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class SubjectOut(BaseModel):
    id: int
    user_id: int
    name: str
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
