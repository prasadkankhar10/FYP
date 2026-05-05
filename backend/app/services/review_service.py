"""
services/review_service.py — Core review processing business logic.
Selects the correct algorithm and updates scheduling state + logs.
Algorithm modules are imported here (will be implemented in Steps 5–7).
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.concept import Concept
from app.models.scheduling import SchedulingData
from app.models.review_log import ReviewLog
from app.schemas.review import ReviewSubmit


def process_review(
    db: Session,
    user: User,
    concept: Concept,
    sched: SchedulingData,
    payload: ReviewSubmit,
) -> ReviewLog:
    """
    Process a review submission:
    1. Compute current retrievability R (for logging)
    2. Run the appropriate algorithm to get updated scheduling state
    3. Save the ReviewLog
    4. Update SchedulingData
    """
    from app.algorithms.scheduler import run_algorithm

    # Compute current R before updating (for analytics)
    retention_at_review = sched.retrievability

    # Run the algorithm: returns updated fields dict
    updated = run_algorithm(sched, payload.quality_score, concept=concept, db=db)

    # Update scheduling data
    sched.ease_factor = updated.get("ease_factor", sched.ease_factor)
    sched.interval_days = updated.get("interval_days", sched.interval_days)
    sched.repetitions = updated.get("repetitions", sched.repetitions)
    sched.stability = updated.get("stability", sched.stability)
    sched.difficulty_fsrs = updated.get("difficulty_fsrs", sched.difficulty_fsrs)
    sched.retrievability = updated.get("retrievability", sched.retrievability)
    sched.next_review_date = updated["next_review_date"]
    sched.last_review_date = datetime.now(timezone.utc)

    # Create review log entry
    log = ReviewLog(
        concept_id=concept.id,
        user_id=user.id,
        algorithm_used=sched.algorithm,
        quality_score=payload.quality_score,
        response_time_sec=payload.response_time_sec,
        was_correct=payload.was_correct,
        retention_at_review=retention_at_review,
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
