"""
algorithms/propagation.py — Stability Propagation Engine.
When a concept is reviewed, the change in stability (ΔS) is propagated
to its 1-hop neighbors in the knowledge graph.

Propagation rules:
  - On FAILURE (rating=1): negative propagation with factor 0.15
    "If you forgot derivatives, your knowledge of integrals is probably shaky too"
  - On SUCCESS (rating≥3): positive propagation with smaller factor 0.05
    "If you nailed derivatives, your integral foundation is slightly reinforced"
  - On HARD (rating=2): no propagation (marginal performance doesn't signal much)

Safety guards:
  - propagation_factor hard-capped at 0.20
  - Only 1-hop (no cascading to neighbors-of-neighbors)
  - Stability floor of 0.4 days (neighbor can't go below this)
  - Sum of outgoing weights ≤ 1.0 (enforced by GraphManager normalization)
"""
import json
from typing import List, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.scheduling import SchedulingData
from app.models.propagation_log import PropagationLog
from app.algorithms.knowledge_graph import GraphManager, WeightConfig, DEFAULT_CONFIG


class PropagationEngine:
    """
    Handles stability propagation from a reviewed concept to its graph neighbors.
    All methods are classmethods — no instance state.
    """

    @classmethod
    def propagate(
        cls,
        db: Session,
        user_id: int,
        concept_id: int,
        delta_S: float,
        rating: int,
        config: WeightConfig = None
    ) -> List[Tuple[int, float]]:
        """
        Propagate the stability change (ΔS) from a reviewed concept to its neighbors.

        Args:
            db: Database session
            user_id: Current user
            concept_id: The concept that was just reviewed
            delta_S: Change in stability = S_new - S_old
            rating: The review rating (1=Again, 2=Hard, 3=Good, 4=Easy)
            config: Weight configuration (uses DEFAULT_CONFIG if not provided)

        Returns:
            List of (target_concept_id, delta_applied) tuples showing what was propagated.
        """
        if config is None:
            config = DEFAULT_CONFIG

        # Rating 2 (Hard) → no propagation. Marginal performance is ambiguous.
        if rating == 2:
            return []

        # Determine propagation factor based on success/failure
        if rating == 1:
            # FAILURE: stronger propagation (negative ΔS carries more signal)
            prop_factor = min(config.propagation_factor_fail, config.propagation_factor_cap)
        else:
            # SUCCESS (rating 3 or 4): weaker propagation
            prop_factor = min(config.propagation_factor_pass, config.propagation_factor_cap)

        # Get 1-hop neighbors
        edges = GraphManager.get_neighbors(db, concept_id, user_id, config)
        if not edges:
            return []

        results = []
        for edge in edges:
            # Compute the delta to apply to this neighbor
            # ΔS_neighbor = w_final * ΔS * propagation_factor
            delta_neighbor = edge.w_final * delta_S * prop_factor

            # Skip negligible deltas (< 0.001 stability change is noise)
            if abs(delta_neighbor) < 0.001:
                continue

            # Fetch the neighbor's scheduling data
            neighbor_sched = (
                db.query(SchedulingData)
                .filter(
                    SchedulingData.concept_id == edge.target_concept_id,
                    SchedulingData.user_id == user_id,
                )
                .first()
            )
            if not neighbor_sched:
                continue

            old_stability = neighbor_sched.stability

            # Apply the delta with safety floor and dampening
            # Dampening: Don't let a single propagation event wipe out more than 20% of existing stability
            if delta_neighbor < 0:
                max_loss = -0.20 * old_stability
                delta_neighbor = max(delta_neighbor, max_loss)

            new_stability = old_stability + delta_neighbor
            new_stability = max(config.stability_floor, new_stability)
            new_stability = round(new_stability, 4)

            # Only update if there's a meaningful change
            if abs(new_stability - old_stability) < 0.001:
                continue

            # Update neighbor's scheduling data
            neighbor_sched.stability = new_stability
            neighbor_sched.interval_days = max(1, round(new_stability))
            neighbor_sched.next_review_date = (
                datetime.now(timezone.utc) + timedelta(days=neighbor_sched.interval_days)
            )

            # Determine event type for logging
            event_type = "negative_propagation" if delta_neighbor < 0 else "positive_propagation"

            # Log the propagation event
            log = PropagationLog(
                user_id=user_id,
                source_concept_id=concept_id,
                target_concept_id=edge.target_concept_id,
                event_type=event_type,
                delta_stability=round(delta_neighbor, 6),
                w_final_used=edge.w_final,
                details=json.dumps({
                    "rating": rating,
                    "prop_factor": prop_factor,
                    "old_stability": old_stability,
                    "new_stability": new_stability,
                    "delta_S_source": round(delta_S, 4),
                }),
            )
            db.add(log)

            results.append((edge.target_concept_id, round(delta_neighbor, 6)))

        if results:
            db.flush()

        return results

    @classmethod
    def get_avg_neighbor_retrievability(
        cls,
        db: Session,
        concept_id: int,
        user_id: int,
        config: WeightConfig = None
    ) -> float:
        """
        Compute the average retrievability of a concept's neighbors.
        Used by multi_fsrs to adjust scheduling intervals based on graph health.

        Returns:
            Average R of neighbors, or 1.0 if no neighbors (neutral = no adjustment).
        """
        if config is None:
            config = DEFAULT_CONFIG

        edges = GraphManager.get_neighbors(db, concept_id, user_id, config)
        if not edges:
            return 1.0  # No neighbors → no graph adjustment

        retrievabilities = []
        for edge in edges:
            neighbor_sched = (
                db.query(SchedulingData)
                .filter(
                    SchedulingData.concept_id == edge.target_concept_id,
                    SchedulingData.user_id == user_id,
                )
                .first()
            )
            if neighbor_sched:
                retrievabilities.append(neighbor_sched.retrievability)

        if not retrievabilities:
            return 1.0

        return sum(retrievabilities) / len(retrievabilities)
