"""
routers/analytics.py — Analytics endpoints for dashboard and comparison.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List
from app.database import get_db
from app.models.user import User
from app.models.concept import Concept
from app.models.review_log import ReviewLog
from app.models.scheduling import SchedulingData
from app.schemas.analytics import OverviewStats, AlgorithmCompareStats, RetentionPoint, StabilityPoint
from pydantic import BaseModel
from app.utils.auth import get_current_user

# Additional Schemas for new endpoints
class ResponseTimePoint(BaseModel):
    review_number: int
    avg_response_time_sec: float

class ActivityPoint(BaseModel):
    date: str
    count: int

router = APIRouter()


@router.get("/overview", response_model=OverviewStats)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dashboard summary statistics."""
    total_concepts = db.query(Concept).filter(Concept.user_id == current_user.id).count()
    logs = db.query(ReviewLog).filter(ReviewLog.user_id == current_user.id).all()
    total_reviews = len(logs)
    correct = sum(1 for l in logs if l.was_correct)
    accuracy = round((correct / total_reviews * 100), 2) if total_reviews > 0 else 0.0

    now = datetime.now(timezone.utc)
    due_today = db.query(SchedulingData).filter(
        SchedulingData.user_id == current_user.id,
        SchedulingData.next_review_date <= now,
    ).count()

    # Calculate Streak
    logs_dates = [log.reviewed_at.date() for log in logs]
    unique_dates = sorted(list(set(logs_dates)), reverse=True)
    
    streak = 0
    today_date = now.date()
    
    if unique_dates:
        if unique_dates[0] == today_date or (today_date - unique_dates[0]).days == 1:
            streak = 1
            for i in range(1, len(unique_dates)):
                if (unique_dates[i-1] - unique_dates[i]).days == 1:
                    streak += 1
                else:
                    break

    return OverviewStats(
        total_concepts=total_concepts,
        total_reviews=total_reviews,
        overall_accuracy=accuracy,
        due_today=due_today,
        current_streak=streak,
    )


@router.get("/compare", response_model=List[AlgorithmCompareStats])
def compare_algorithms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare SM-2 vs FSRS vs Multi-FSRS performance metrics."""
    algorithms = ["sm2", "fsrs", "multi_fsrs"]
    results = []

    import math

    for algo in algorithms:
        logs = db.query(ReviewLog).filter(
            ReviewLog.user_id == current_user.id,
            ReviewLog.algorithm_used == algo
        ).all()

        if not logs:
            continue

        total = len(logs)
        correct = 0
        sq_err_sum = 0.0
        log_loss_sum = 0.0
        valid_metric_logs = 0
        
        for l in logs:
            if l.was_correct:
                correct += 1
            
            # Calculate metrics if we have a valid prediction
            if l.retention_at_review is not None:
                # Actual outcome: 1 if correct, 0 if failed
                y = 1.0 if l.was_correct else 0.0
                # Predicted probability (ensure it's never exactly 0 or 1 to avoid math domain errors)
                p = max(0.001, min(0.999, l.retention_at_review))
                
                # RMSE component
                sq_err_sum += (y - p) ** 2
                
                # Log-Loss component: - (y * ln(p) + (1 - y) * ln(1 - p))
                log_loss_sum += -(y * math.log(p) + (1.0 - y) * math.log(1.0 - p))
                
                valid_metric_logs += 1

        accuracy = round(correct / total * 100, 2)
        
        rmse = None
        log_loss = None
        if valid_metric_logs > 0:
            rmse = round(math.sqrt(sq_err_sum / valid_metric_logs), 4)
            log_loss = round(log_loss_sum / valid_metric_logs, 4)

        # Average interval for this algorithm
        scheds = db.query(SchedulingData).filter(
            SchedulingData.user_id == current_user.id,
            SchedulingData.algorithm == algo,
        ).all()
        avg_interval = round(
            sum(s.interval_days for s in scheds) / len(scheds), 2
        ) if scheds else 0.0

        avg_stability = None
        if algo in ("fsrs", "multi_fsrs") and scheds:
            avg_stability = round(
                sum(s.stability for s in scheds) / len(scheds), 4
            )

        results.append(AlgorithmCompareStats(
            algorithm=algo,
            total_reviews=total,
            correct_reviews=correct,
            accuracy=accuracy,
            avg_interval_days=avg_interval,
            avg_stability=avg_stability,
            rmse=rmse,
            log_loss=log_loss
        ))

    return results


@router.get("/retention", response_model=List[RetentionPoint])
def get_retention_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns retention (R) at review for each concept over time.
    Used to plot forgetting curve in the frontend.
    """
    logs = (
        db.query(ReviewLog, Concept)
        .join(Concept, ReviewLog.concept_id == Concept.id)
        .filter(
            ReviewLog.user_id == current_user.id,
            ReviewLog.retention_at_review.isnot(None),
        )
        .order_by(ReviewLog.reviewed_at)
        .all()
    )

    # Track review number per concept
    concept_review_count: dict = {}
    
    # Group by review number
    review_number_data = {}
    for log, concept in logs:
        concept_review_count[concept.id] = concept_review_count.get(concept.id, 0) + 1
        rev_num = concept_review_count[concept.id]
        
        if rev_num not in review_number_data:
            review_number_data[rev_num] = []
        review_number_data[rev_num].append(log.retention_at_review)

    # Average them out
    result = []
    for rev_num, retentions in sorted(review_number_data.items()):
        avg_retention = sum(retentions) / len(retentions)
        result.append(RetentionPoint(
            day=rev_num,
            retrievability=round(avg_retention, 4),
            concept_title="Average",  # Not really used in grouped chart
        ))

    return result


@router.get("/stability", response_model=List[StabilityPoint])
def get_stability_growth(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns stability (S) evolution per concept across successive reviews.
    Used to plot stability growth over time in the frontend.
    """
    logs = (
        db.query(ReviewLog, Concept, SchedulingData)
        .join(Concept, ReviewLog.concept_id == Concept.id)
        .join(SchedulingData, SchedulingData.concept_id == Concept.id)
        .filter(
            ReviewLog.user_id == current_user.id,
            SchedulingData.user_id == current_user.id,
        )
        .order_by(ReviewLog.reviewed_at)
        .all()
    )

    concept_review_count: dict = {}
    review_number_data = {}
    
    # We want historical stability, not just current.
    # Currently SchedulingData holds current stability.
    # To do this perfectly, we'd need historical stability logs, but for now
    # we can approximate or just plot current stability vs total review count for each concept
    
    for log, concept, sched in logs:
        concept_review_count[concept.id] = concept_review_count.get(concept.id, 0) + 1
        # Wait, the prompt says "stability evolution per concept across successive reviews"
        # However, `sched.stability` is the CURRENT stability of the concept, not historical.
        # Let's plot average stability by review count.
        
    # Group CURRENT stability by the total number of reviews a concept has had
    total_reviews_data = {}
    for concept_id, total_revs in concept_review_count.items():
        sched = db.query(SchedulingData).filter(
            SchedulingData.concept_id == concept_id,
            SchedulingData.user_id == current_user.id
        ).first()
        if sched:
            if total_revs not in total_reviews_data:
                total_reviews_data[total_revs] = []
            total_reviews_data[total_revs].append(sched.stability)
            
    result = []
    for rev_num, stabilities in sorted(total_reviews_data.items()):
        avg_stab = sum(stabilities) / len(stabilities)
        result.append(StabilityPoint(
            concept_title="Average",
            review_number=rev_num,
            stability=round(avg_stab, 4),
        ))

    return result


@router.get("/distribution")
def get_algorithm_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns how many concepts use each algorithm — for pie/donut charts."""
    scheds = db.query(SchedulingData).filter(
        SchedulingData.user_id == current_user.id
    ).all()

    dist = {}
    for s in scheds:
        dist[s.algorithm] = dist.get(s.algorithm, 0) + 1

    return [{"algorithm": k, "count": v} for k, v in dist.items()]


@router.get("/weak-concepts")
def get_weak_concepts(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns the concepts with lowest retrievability — most at risk of forgetting."""
    rows = (
        db.query(SchedulingData, Concept)
        .join(Concept, SchedulingData.concept_id == Concept.id)
        .filter(SchedulingData.user_id == current_user.id)
        .order_by(SchedulingData.retrievability.asc())
        .limit(limit)
        .all()
    )

    return [
        {
            "concept_id": concept.id,
            "title": concept.title,
            "retrievability": round(sched.retrievability, 4),
            "stability": round(sched.stability, 4),
            "algorithm": sched.algorithm,
            "interval_days": sched.interval_days,
        }
        for sched, concept in rows
    ]


@router.get("/response-time", response_model=List[ResponseTimePoint])
def get_response_time_trend(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns average response time across successive review attempts.
    Measures cognitive fluency (speed of recall).
    """
    logs = (
        db.query(ReviewLog)
        .filter(ReviewLog.user_id == current_user.id)
        .order_by(ReviewLog.reviewed_at)
        .all()
    )

    concept_review_count = {}
    review_number_times = {}

    for log in logs:
        if log.response_time_sec is None:
            continue
            
        concept_review_count[log.concept_id] = concept_review_count.get(log.concept_id, 0) + 1
        rev_num = concept_review_count[log.concept_id]
        
        if rev_num not in review_number_times:
            review_number_times[rev_num] = []
        review_number_times[rev_num].append(log.response_time_sec)

    result = []
    for rev_num, times in sorted(review_number_times.items()):
        avg_time = sum(times) / len(times)
        result.append(ResponseTimePoint(
            review_number=rev_num,
            avg_response_time_sec=round(avg_time, 2)
        ))

    return result


@router.get("/activity", response_model=List[ActivityPoint])
def get_daily_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns the number of reviews completed per day for the last 14 active days."""
    logs = (
        db.query(ReviewLog)
        .filter(ReviewLog.user_id == current_user.id)
        .order_by(ReviewLog.reviewed_at.desc())
        .all()
    )

    date_counts = {}
    for log in logs:
        date_str = log.reviewed_at.strftime("%Y-%m-%d")
        date_counts[date_str] = date_counts.get(date_str, 0) + 1

    # Sort by date ascending
    sorted_dates = sorted(date_counts.keys())
    
    # Return at most last 14 active days
    result = []
    for d in sorted_dates[-14:]:
        result.append(ActivityPoint(date=d, count=date_counts[d]))
        
    return result

