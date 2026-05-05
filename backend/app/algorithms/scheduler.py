"""
algorithms/scheduler.py — Algorithm dispatcher.
Routes scheduling computation to the correct algorithm based on sched.algorithm.
"""
from app.models.scheduling import SchedulingData
from app.algorithms import sm2, fsrs, multi_fsrs


def run_algorithm(sched: SchedulingData, quality_score: int, concept=None, db=None) -> dict:
    """
    Dispatch to the correct scheduling algorithm.
    Returns a dict of updated scheduling fields + next_review_date.
    """
    if sched.algorithm == "sm2":
        return sm2.calculate(sched, quality_score)
    elif sched.algorithm == "fsrs":
        return fsrs.calculate(sched, quality_score)
    elif sched.algorithm == "multi_fsrs":
        return multi_fsrs.calculate(sched, quality_score, concept=concept, db=db)
    else:
        raise ValueError(f"Unknown algorithm: {sched.algorithm}")
