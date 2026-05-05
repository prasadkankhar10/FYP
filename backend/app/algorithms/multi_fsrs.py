"""
algorithms/multi_fsrs.py — Multi-Concept FSRS with Hybrid Knowledge Graph.
EXTENDS standard FSRS by making concepts graph-aware:

Architecture:
  1. Run standard FSRS math on the reviewed concept (unchanged)
  2. Compute ΔS = S_new - S_old
  3. Propagate ΔS to 1-hop neighbors via PropagationEngine
  4. Update co-review/co-failure data signals via SessionTracker
  5. Adjust the reviewed concept's interval based on neighbor health

The key insight: FSRS calculates memory independently per concept. This extension
adds a graph layer that models concept DEPENDENCIES — if you forget calculus,
your probability of remembering differential equations should decrease too.

IMPORTANT: Standard FSRS math is NEVER modified. This is purely an extension layer.
The propagation affects NEIGHBORS, not the reviewed concept's core S/D/R values.
Only the INTERVAL is adjusted based on graph context (neighbor health).
"""
import math
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.scheduling import SchedulingData
from app.algorithms.fsrs import calculate as fsrs_calculate
from app.algorithms.propagation import PropagationEngine
from app.algorithms.session_tracker import SessionTracker
from app.algorithms.knowledge_graph import DEFAULT_CONFIG


def calculate(sched: SchedulingData, rating: int, concept=None, db: Session = None) -> dict:
    """
    Execute Multi-Concept FSRS: standard FSRS + graph propagation + scheduling adjustment.

    Args:
        sched: Current scheduling data for the concept
        rating: Review rating (1=Again, 2=Hard, 3=Good, 4=Easy)
        concept: The Concept ORM object (needed for graph lookups)
        db: Database session (needed for graph operations)

    Returns:
        Dict of updated scheduling fields, same shape as standard FSRS output.
    """
    # ──────────────────────────────────────────────────────────────────────────
    # Step 1: Run standard FSRS math (NEVER modified)
    # ──────────────────────────────────────────────────────────────────────────
    old_stability = sched.stability
    updated = fsrs_calculate(sched, rating)
    new_stability = updated["stability"]

    # ──────────────────────────────────────────────────────────────────────────
    # Step 2: Compute stability delta
    # ──────────────────────────────────────────────────────────────────────────
    delta_S = new_stability - old_stability

    # ──────────────────────────────────────────────────────────────────────────
    # Steps 3-5: Graph operations (only if we have DB access and a concept)
    # ──────────────────────────────────────────────────────────────────────────
    if db is not None and concept is not None:
        try:
            # Step 3: Propagate ΔS to graph neighbors
            PropagationEngine.propagate(
                db=db,
                user_id=sched.user_id,
                concept_id=concept.id,
                delta_S=delta_S,
                rating=rating,
                config=DEFAULT_CONFIG,
            )

            # Step 4: Update co-review/co-failure data signals
            SessionTracker.update_co_signals(
                db=db,
                user_id=sched.user_id,
                concept_id=concept.id,
                rating=rating,
                config=DEFAULT_CONFIG,
            )

            # Step 5: Adjust interval based on neighbor health
            avg_neighbor_R = PropagationEngine.get_avg_neighbor_retrievability(
                db=db,
                concept_id=concept.id,
                user_id=sched.user_id,
                config=DEFAULT_CONFIG,
            )
            updated = _adjust_interval_for_graph_context(updated, avg_neighbor_R)

        except Exception as e:
            # Graph operations should NEVER break the core FSRS update.
            # If anything goes wrong, log it and return standard FSRS result.
            print(f"[Multi-FSRS] Graph operation failed (non-fatal): {e}")

    return updated


def _adjust_interval_for_graph_context(updated: dict, avg_neighbor_R: float) -> dict:
    """
    Adjust the reviewed concept's interval based on how healthy its graph
    neighborhood is. This is a SCHEDULING adjustment, not a stability change.

    Intuition:
      - If your neighbors are weak (low R), you should review sooner because
        the broader knowledge context is fragile.
      - If your neighbors are strong (high R), you can afford a slightly
        longer interval because the foundation is solid.

    Rules:
      - avg_neighbor_R < 0.5  → reduce interval by 15% (weak context)
      - avg_neighbor_R > 0.85 → increase interval by 10% (strong context)
      - Otherwise → no adjustment (neutral zone)

    The 1.0 sentinel from PropagationEngine means "no neighbors" → no adjustment.
    """
    interval = updated["interval_days"]

    # No neighbors or neutral → no adjustment
    if avg_neighbor_R >= 1.0:
        return updated

    if avg_neighbor_R < 0.5:
        # Weak graph context: reduce interval to reinforce sooner
        adjustment = 0.85  # -15%
    elif avg_neighbor_R > 0.85:
        # Strong graph context: can afford slightly longer interval
        adjustment = 1.10  # +10%
    else:
        # Neutral zone: no adjustment
        return updated

    adjusted_interval = max(1, round(interval * adjustment))

    # Only update if interval actually changed
    if adjusted_interval != interval:
        updated["interval_days"] = adjusted_interval
        updated["next_review_date"] = (
            datetime.now(timezone.utc) + timedelta(days=adjusted_interval)
        )

    return updated
