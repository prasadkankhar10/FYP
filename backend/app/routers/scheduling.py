"""
routers/scheduling.py — Scheduling management endpoints.
GET  /schedule/today       — today's sorted review queue
POST /schedule/algorithm   — switch active algorithm for a concept
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from app.database import get_db
from app.models.user import User
from app.models.concept import Concept
from app.models.subject import Subject
from app.models.scheduling import SchedulingData
from app.schemas.review import DueConceptOut, AlgorithmSwitch, SchedulingDataOut
from app.utils.auth import get_current_user
from app.utils.exceptions import not_found, bad_request

router = APIRouter()

VALID_ALGORITHMS = {"sm2", "fsrs", "multi_fsrs"}


@router.get("/today", response_model=List[DueConceptOut])
def get_today_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns today's review queue for the user.
    Multi-FSRS: sorted by priority (lowest retrievability first).
    SM-2/FSRS: sorted by due date.
    """
    now = datetime.now(timezone.utc)

    rows = (
        db.query(SchedulingData, Concept, Subject)
        .join(Concept, SchedulingData.concept_id == Concept.id)
        .join(Subject, Concept.subject_id == Subject.id)
        .filter(
            SchedulingData.user_id == current_user.id,
            SchedulingData.next_review_date <= now,
        )
        .all()
    )

    result = []
    for sched, concept, subject in rows:
        # Priority score: lower retrievability = higher urgency
        priority = 1.0 - sched.retrievability if sched.algorithm == "multi_fsrs" else 0.0
        result.append(DueConceptOut(
            concept_id=concept.id,
            concept_title=concept.title,
            subject_name=subject.name,
            algorithm=sched.algorithm,
            next_review_date=sched.next_review_date,
            retrievability=sched.retrievability,
            interval_days=sched.interval_days,
            priority_score=round(priority, 4),
        ))

    # Sort: multi_fsrs by priority desc; others by due date asc
    result.sort(key=lambda x: -x.priority_score if x.algorithm == "multi_fsrs" else 0)
    return result


@router.post("/algorithm/{concept_id}")
def switch_algorithm(
    concept_id: int,
    payload: AlgorithmSwitch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Switch the active scheduling algorithm for a specific concept."""
    if payload.algorithm not in VALID_ALGORITHMS:
        raise bad_request(f"Algorithm must be one of: {', '.join(VALID_ALGORITHMS)}")

    sched = db.query(SchedulingData).filter(
        SchedulingData.concept_id == concept_id,
        SchedulingData.user_id == current_user.id,
    ).first()
    if not sched:
        raise not_found("Scheduling data")

    sched.algorithm = payload.algorithm
    db.commit()
    return {"message": f"Algorithm switched to {payload.algorithm} for concept {concept_id}"}


@router.get("/{concept_id}", response_model=SchedulingDataOut)
def get_scheduling_data(
    concept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get full scheduling state for a concept."""
    sched = db.query(SchedulingData).filter(
        SchedulingData.concept_id == concept_id,
        SchedulingData.user_id == current_user.id,
    ).first()
    if not sched:
        raise not_found("Scheduling data")
    return sched
