"""
routers/subjects.py — Subject CRUD endpoints.
All routes require authentication.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.subject import Subject
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectOut
from app.utils.auth import get_current_user
from app.utils.exceptions import not_found, forbidden

router = APIRouter()


@router.get("/", response_model=List[SubjectOut])
def list_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all subjects belonging to the current user."""
    return db.query(Subject).filter(Subject.user_id == current_user.id).all()


@router.post("/", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(
    payload: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new subject."""
    subject = Subject(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
    )
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.put("/{subject_id}", response_model=SubjectOut)
def update_subject(
    subject_id: int,
    payload: SubjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a subject's name or description."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise not_found("Subject")
    if subject.user_id != current_user.id:
        raise forbidden()

    if payload.name is not None:
        subject.name = payload.name
    if payload.description is not None:
        subject.description = payload.description

    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a subject and all its concepts (cascade)."""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise not_found("Subject")
    if subject.user_id != current_user.id:
        raise forbidden()
    db.delete(subject)
    db.commit()
