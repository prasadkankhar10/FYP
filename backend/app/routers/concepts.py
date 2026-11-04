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
    try:
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
        
        # Auto-link parent concept via semantic embeddings if not explicitly provided
        if not concept.parent_concept_id:
            try:
                existing = db.query(Concept).filter(Concept.subject_id == concept.subject_id, Concept.id != concept.id).all()
                if existing:
                    from app.utils.embeddings import find_closest_concept
                    candidates = [(c.id, f"{c.title} {c.content or ''}") for c in existing]
                    best_parent_id = find_closest_concept(f"{concept.title} {concept.content or ''}", candidates)
                    if best_parent_id:
                        concept.parent_concept_id = best_parent_id
                        db.add(concept)
                        db.flush()
            except Exception as e:
                print(f"Warning: Auto-linking parent concept failed: {e}")

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
            except Exception as e:
                print(f"Warning: Knowledge graph edge creation skipped: {e}")

        db.commit()
        db.refresh(concept)
        return concept
    except Exception as e:
        db.rollback()
        raise e


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

    try:
        if payload.title is not None:
            concept.title = payload.title
        if payload.content is not None:
            concept.content = payload.content
        if payload.difficulty is not None:
            concept.difficulty = payload.difficulty

        # Handle parent_concept_id (Knowledge Graph edge)
        payload_data = payload.model_dump(exclude_unset=True)
        if 'parent_concept_id' in payload_data:
            new_parent_id = payload_data['parent_concept_id']
            
            # Only perform graph updates if the parent actually changed
            if new_parent_id != concept.parent_concept_id:
                # 1. Remove old edge if there was one
                if concept.parent_concept_id is not None:
                    try:
                        GraphManager.remove_edge(db, current_user.id, concept.parent_concept_id, concept.id)
                    except Exception as e:
                        print(f"Warning: Failed to remove old edge: {e}")
                
                # 2. Add new edge if there is a new parent
                if new_parent_id is not None:
                    try:
                        GraphManager.add_edge(
                            db=db,
                            user_id=current_user.id,
                            source_id=new_parent_id,
                            target_id=concept.id,
                            w_expert=0.6,
                        )
                    except Exception as e:
                        print(f"Warning: Failed to add new edge: {e}")
                
                # 3. Update the concept column
                concept.parent_concept_id = new_parent_id

        db.commit()
        db.refresh(concept)
        return concept
    except Exception as e:
        db.rollback()
        raise e


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


@router.get("/export/all")
def export_concepts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export all user concepts and scheduling data for backup."""
    concepts = db.query(Concept).filter(Concept.user_id == current_user.id).all()
    data = []
    for c in concepts:
        sched = db.query(SchedulingData).filter(SchedulingData.concept_id == c.id).first()
        data.append({
            "title": c.title,
            "content": c.content,
            "difficulty": c.difficulty,
            "subject_id": c.subject_id,
            "scheduling": {
                "algorithm": sched.algorithm if sched else "sm2",
                "stability": sched.stability if sched else 0.0,
                "difficulty_fsrs": sched.difficulty_fsrs if sched else 5.0,
                "interval_days": sched.interval_days if sched else 0,
            } if sched else None
        })
    return {"concepts": data}


@router.post("/import/all")
def import_concepts(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import concepts from a JSON payload."""
    concepts_data = payload.get("concepts", [])
    imported_count = 0
    
    for c_data in concepts_data:
        # Simple import: just create new concepts
        concept = Concept(
            user_id=current_user.id,
            subject_id=c_data.get("subject_id"),
            title=c_data.get("title"),
            content=c_data.get("content"),
            difficulty=c_data.get("difficulty", "medium")
        )
        db.add(concept)
        db.flush()
        
        s_data = c_data.get("scheduling", {})
        sched = SchedulingData(
            concept_id=concept.id,
            user_id=current_user.id,
            algorithm=s_data.get("algorithm", "sm2"),
            stability=s_data.get("stability", 0.0),
            difficulty_fsrs=s_data.get("difficulty_fsrs", 5.0),
            interval_days=s_data.get("interval_days", 0),
            next_review_date=datetime.now(timezone.utc),
            retrievability=1.0
        )
        db.add(sched)
        imported_count += 1
        
    db.commit()
    return {"success": True, "imported": imported_count}


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
