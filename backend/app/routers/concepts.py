"""
routers/concepts.py — Concept and QuizQuestion CRUD endpoints.
When a concept is created, a SchedulingData row is automatically initialized.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
import random
from app.database import get_db
from app.models.user import User
from app.models.concept import Concept
from app.models.quiz_question import QuizQuestion
from app.models.scheduling import SchedulingData
from app.schemas.concept import ConceptCreate, ConceptUpdate, ConceptOut
from app.schemas.concept import QuizQuestionCreate, QuizQuestionOut
from app.utils.auth import get_current_user
from app.utils.exceptions import not_found, forbidden
from app.algorithms.knowledge_graph import GraphManager

router = APIRouter()


@router.get("/", response_model=List[ConceptOut])
def list_concepts(
    subject_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List concepts. Optionally filter by subject_id."""
    query = db.query(Concept).filter(Concept.user_id == current_user.id)
    if subject_id:
        query = query.filter(Concept.subject_id == subject_id)
    return query.all()


@router.post("/", response_model=ConceptOut, status_code=status.HTTP_201_CREATED)
def create_concept(
    payload: ConceptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new concept.
    Auto-initializes SchedulingData with SM-2 defaults for both sm2 and fsrs.
    """
    concept = Concept(
        subject_id=payload.subject_id,
        user_id=current_user.id,
        title=payload.title,
        content=payload.content,
        difficulty=payload.difficulty or "medium",
        parent_concept_id=getattr(payload, 'parent_concept_id', None),
    )
    db.add(concept)
    db.flush()  # Get concept.id without committing

    # Auto-create scheduling entry for this concept (SM-2 defaults)
    sched = SchedulingData(
        concept_id=concept.id,
        user_id=current_user.id,
        algorithm=random.choice(["sm2", "fsrs", "multi_fsrs"]),
        ease_factor=2.5,
        interval_days=1,
        repetitions=0,
        stability=0.0,
        difficulty_fsrs=5.0,
        retrievability=1.0,
        next_review_date=datetime.now(timezone.utc),
    )
    db.add(sched)
    db.flush()

    # Auto-create knowledge graph edge if this concept has a parent
    if concept.parent_concept_id is not None:
        try:
            GraphManager.add_edge(
                db=db,
                user_id=current_user.id,
                source_id=concept.parent_concept_id,
                target_id=concept.id,
                w_expert=0.6,  # Parent-child edges get slightly higher expert weight
            )
        except ValueError:
            pass  # Edge already exists or neighbor limit reached — not critical

    db.commit()
    db.refresh(concept)
    return concept


@router.get("/{concept_id}", response_model=ConceptOut)
def get_concept(
    concept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    if not concept:
        raise not_found("Concept")
    if concept.user_id != current_user.id:
        raise forbidden()
    return concept


@router.put("/{concept_id}", response_model=ConceptOut)
def update_concept(
    concept_id: int,
    payload: ConceptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    if not concept:
        raise not_found("Concept")
    if concept.user_id != current_user.id:
        raise forbidden()

    if payload.title is not None:
        concept.title = payload.title
    if payload.content is not None:
        concept.content = payload.content
    if payload.difficulty is not None:
        concept.difficulty = payload.difficulty

    db.commit()
    db.refresh(concept)
    return concept


@router.delete("/{concept_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_concept(
    concept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.models.concept_edge import ConceptEdge
    from app.models.propagation_log import PropagationLog

    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    if not concept:
        raise not_found("Concept")
    if concept.user_id != current_user.id:
        raise forbidden()

    # Clean up graph edges (both directions) and propagation logs
    db.query(ConceptEdge).filter(
        (ConceptEdge.source_concept_id == concept_id) |
        (ConceptEdge.target_concept_id == concept_id)
    ).delete(synchronize_session="fetch")

    db.query(PropagationLog).filter(
        (PropagationLog.source_concept_id == concept_id) |
        (PropagationLog.target_concept_id == concept_id)
    ).delete(synchronize_session="fetch")

    db.delete(concept)
    db.commit()


# ── Quiz Questions ─────────────────────────────────────────────────────────────

@router.post("/{concept_id}/questions", response_model=QuizQuestionOut, status_code=201)
def add_question(
    concept_id: int,
    payload: QuizQuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a quiz question to a concept."""
    concept = db.query(Concept).filter(
        Concept.id == concept_id, Concept.user_id == current_user.id
    ).first()
    if not concept:
        raise not_found("Concept")

    q = QuizQuestion(
        concept_id=concept_id,
        question_text=payload.question_text,
        question_type=payload.question_type,
        options=payload.options,
        correct_answer=payload.correct_answer,
        difficulty_level=payload.difficulty_level,
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return q


@router.get("/{concept_id}/questions", response_model=List[QuizQuestionOut])
def get_questions(
    concept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all quiz questions for a concept."""
    concept = db.query(Concept).filter(
        Concept.id == concept_id, Concept.user_id == current_user.id
    ).first()
    if not concept:
        raise not_found("Concept")
    return db.query(QuizQuestion).filter(QuizQuestion.concept_id == concept_id).all()
