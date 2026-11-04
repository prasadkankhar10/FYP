"""
routers/reviews.py — Review submission and history endpoints.
POST /reviews/submit  — submit a review result (triggers scheduling update)
GET  /reviews/due     — get concepts due for review
GET  /reviews/history — past review logs
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models.user import User
from app.models.concept import Concept
from app.models.review_log import ReviewLog
from app.models.scheduling import SchedulingData
from app.models.subject import Subject
from app.schemas.review import ReviewSubmit, ReviewLogOut, DueConceptOut
from app.utils.auth import get_current_user
from app.utils.exceptions import not_found, bad_request
from app.services.review_service import process_review

router = APIRouter()


@router.post("/submit", response_model=ReviewLogOut)
def submit_review(
    payload: ReviewSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a review result for a concept.
    This triggers the algorithm (SM-2 or FSRS) to update the next review date.
    """
    concept = db.query(Concept).filter(
        Concept.id == payload.concept_id,
        Concept.user_id == current_user.id
    ).first()
    if not concept:
        raise not_found("Concept")

    sched = db.query(SchedulingData).filter(
        SchedulingData.concept_id == concept.id,
        SchedulingData.user_id == current_user.id
    ).first()
    if not sched:
        raise bad_request("No scheduling data found. Re-add the concept.")

    # Validate quality score based on algorithm
    if sched.algorithm == "sm2" and not (0 <= payload.quality_score <= 5):
        raise bad_request("SM-2 quality score must be 0–5.")
    if sched.algorithm in ("fsrs", "multi_fsrs") and not (1 <= payload.quality_score <= 4):
        raise bad_request("FSRS rating must be 1–4 (Again/Hard/Good/Easy).")

    # Process the review: run algorithm, update scheduling, create log
    log = process_review(db, current_user, concept, sched, payload)
    return log


@router.get("/due", response_model=List[DueConceptOut])
def get_due_reviews(
    subject_id: Optional[int] = None,
    include_all: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get concepts due for review today (next_review_date <= now).
    If subject_id is provided, filters strictly for concepts within that subject.
    If no reviews are due today for that subject (or include_all is True), fetches all concepts for that subject sorted by lowest retrievability.
    """
    now = datetime.now(timezone.utc)
    query = (
        db.query(SchedulingData, Concept, Subject)
        .join(Concept, SchedulingData.concept_id == Concept.id)
        .join(Subject, Concept.subject_id == Subject.id)
        .filter(SchedulingData.user_id == current_user.id)
    )

    if subject_id:
        query = query.filter(Concept.subject_id == subject_id)

    # First check strictly due reviews
    due_query = query.filter(SchedulingData.next_review_date <= now)
    due = due_query.all()

    # If no cards are strictly due for a chosen subject, or if include_all is requested,
    # fetch all concepts sorted by retrievability/priority so user can practice!
    if (len(due) == 0 and subject_id) or include_all:
        due = query.all()

    result = []
    for sched, concept, subject in due:
        priority_score = 1.0 - (sched.retrievability if sched.retrievability is not None else 1.0)
        if sched.algorithm == "multi_fsrs" and sched.interval_days <= 1:
            priority_score += 2.0

        result.append(DueConceptOut(
            concept_id=concept.id,
            concept_title=concept.title,
            concept_content=concept.content,
            subject_name=subject.name,
            algorithm=sched.algorithm,
            next_review_date=sched.next_review_date,
            retrievability=sched.retrievability if sched.retrievability is not None else 1.0,
            interval_days=sched.interval_days if sched.interval_days is not None else 1,
            priority_score=priority_score,
        ))

    result.sort(key=lambda x: (x.priority_score or 0.0), reverse=True)
    return result


@router.get("/exam/{subject_id}", response_model=List[DueConceptOut])
def get_exam_prep(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Fetch ALL concepts for a specific subject, sorted by lowest retrievability.
    This helps the user focus on what they are most likely to have forgotten before an exam.
    """
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current_user.id).first()
    if not subject:
        raise not_found("Subject")

    # Fetch all concepts and their scheduling data for this subject
    concepts_data = (
        db.query(SchedulingData, Concept)
        .join(Concept, SchedulingData.concept_id == Concept.id)
        .filter(
            Concept.subject_id == subject_id,
            Concept.user_id == current_user.id
        )
        .all()
    )

    result = []
    for sched, concept in concepts_data:
        result.append(DueConceptOut(
            concept_id=concept.id,
            concept_title=concept.title,
            concept_content=concept.content,
            subject_name=subject.name,
            algorithm=sched.algorithm,
            next_review_date=sched.next_review_date,
            retrievability=sched.retrievability,
            interval_days=sched.interval_days,
            priority_score=1.0 - sched.retrievability
        ))

    # Sort by retrievability (lowest first)
    result.sort(key=lambda x: x.retrievability)
    return result


@router.get("/history", response_model=List[ReviewLogOut])
def get_history(
    concept_id: int = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get review history. Optionally filter by concept_id."""
    query = db.query(ReviewLog).filter(ReviewLog.user_id == current_user.id)
    if concept_id:
        query = query.filter(ReviewLog.concept_id == concept_id)
    return query.order_by(ReviewLog.reviewed_at.desc()).limit(limit).all()
