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
    user_fsrs_params = None
    if db:
        from app.models.user import User
        import json
        user = db.query(User).filter(User.id == sched.user_id).first()
        if user and user.fsrs_params:
            try:
                user_fsrs_params = json.loads(user.fsrs_params)
            except:
                user_fsrs_params = None

    if sched.algorithm == "sm2":
        return sm2.calculate(sched, quality_score)
    elif sched.algorithm == "fsrs":
        return fsrs.calculate(sched, quality_score, w_custom=user_fsrs_params)
    elif sched.algorithm == "multi_fsrs":
        return multi_fsrs.calculate(sched, quality_score, concept=concept, db=db, w_custom=user_fsrs_params)
    else:
        raise ValueError(f"Unknown algorithm: {sched.algorithm}")
