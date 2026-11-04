"""
algorithms/fsrs.py — FSRS v4 algorithm implementation.
Calculates optimal intervals using DSR (Difficulty, Stability, Retrievability) modeling.
"""
import math
from datetime import datetime, timedelta, timezone
from app.models.scheduling import SchedulingData

# FSRS v4 Default Weights
w = [
    0.40255, 1.18385, 3.173, 15.69105, 7.1949, 0.5345, 1.4604, 0.0046, 
    1.54575, 0.1192, 1.01925, 1.9395, 0.11, 0.29605, 2.2698, 0.2315, 2.9898
]

def calculate(sched: SchedulingData, rating: int, w_custom: list = None) -> dict:
    """
    Apply FSRS algorithm.
    rating mapping: 1: Again, 2: Hard, 3: Good, 4: Easy
    """
    # Use custom weights if provided, else default
    weights = w_custom if w_custom else w
    
    # Parse inputs
    last_D = sched.difficulty_fsrs if sched.difficulty_fsrs > 0 else 5.0
    last_S = sched.stability
    interval = sched.interval_days
    repetitions = sched.repetitions

    # Calculate Retrievability (R) prior to this review
    # FSRS v4 R decay: R = (1 + I / (9 * S)) ^ -1
    R = 1.0
    if last_S > 0:
        R = math.pow(1 + interval / (9 * last_S), -1)

    # First review logic: initialized S and D based directly on the grade
    if last_S == 0:
        if rating == 1:
            S = weights[0]
        elif rating == 2:
            S = weights[1]
        elif rating == 3:
            S = weights[2]
        else: # 4
            S = weights[3]
        
        D = weights[4] - weights[5] * (rating - 3)
    else:
        # Update difficulty
        D = last_D - weights[6] * (rating - 3)
        
        # Mean reversion for difficulty
        D = D * (1 - weights[7]) + weights[4] * weights[7]
        D = min(max(D, 1.0), 10.0)

        # Update stability
        if rating == 1: # Failed (Again)
            S = weights[11] * math.pow(last_D, -weights[12]) * (math.pow(last_S + 1, weights[13]) - 1) * math.exp(weights[14] * (1 - R))
        else: # Passed (Hard, Good, Easy)
            S = last_S * (1 + math.exp(weights[8]) * (11 - last_D) * math.pow(last_S, -weights[9]) * (math.exp((1 - R) * weights[10]) - 1))
            if rating == 2:
                S *= weights[15]
            elif rating == 4:
                S *= weights[16]

    # By definition of FSRS, Stability (S) is the interval when Retrievability drops to exactly 0.90
    # Because we target 90% retention, interval = S
    next_interval = min(36500, max(1, round(S)))
    
    if rating > 1:
        repetitions += 1
    else:
        repetitions = 0

    return {
        "ease_factor": sched.ease_factor, # Unused in FSRS
        "interval_days": next_interval,
        "repetitions": repetitions,
        "stability": round(S, 4),
        "difficulty_fsrs": round(D, 4),
        "retrievability": round(R, 4),
        "next_review_date": datetime.now(timezone.utc) + timedelta(days=next_interval)
    }
