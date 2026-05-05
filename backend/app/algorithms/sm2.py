"""
algorithms/sm2.py — SM-2 algorithm implementation.
Calculates spaced repetition intervals based on the classic SuperMemo-2 model.
"""
import math
from datetime import datetime, timedelta, timezone
from app.models.scheduling import SchedulingData


def calculate(sched: SchedulingData, quality: int) -> dict:
    """
    Apply the SM-2 algorithm to compute the next interval and EF.
    
    quality mapping (0-5 scale):
    5: perfect response
    4: correct response after a hesitation
    3: correct response recalled with serious difficulty
    2: incorrect response; where the correct one seemed easy to recall
    1: incorrect response; the correct one remembered
    0: complete blackout
    """
    EF = sched.ease_factor
    interval = sched.interval_days
    repetitions = sched.repetitions

    # Update Ease Factor (EF)
    EF = EF + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if EF < 1.3:
        EF = 1.3

    # Calculate optimal interval
    if quality >= 3:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = math.ceil(interval * EF)
        repetitions += 1
    else:
        # If the user failed, reset consecutive repetitions and interval
        repetitions = 0
        interval = 1

    return {
        "ease_factor": round(EF, 3),
        "interval_days": interval,
        "repetitions": repetitions,
        "stability": sched.stability,  # Unchanged in SM-2
        "difficulty_fsrs": sched.difficulty_fsrs,  # Unchanged in SM-2
        "retrievability": sched.retrievability,  # Unchanged in SM-2
        "next_review_date": datetime.now(timezone.utc) + timedelta(days=interval),
    }
