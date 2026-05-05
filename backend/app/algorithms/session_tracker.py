"""
algorithms/session_tracker.py — Co-Review / Co-Failure Data Signal Tracker.
Learns the w_data weight on edges by tracking behavioral correlation:
  - When two connected concepts are both reviewed in the same session window,
    increment co_review_count.
  - When two connected concepts BOTH FAIL in the same session window,
    increment co_fail_count.
  - w_data = co_fail_count / co_review_count (ratio of co-failures)

Session window: reviews within 30 minutes are considered the same session.

Intuition: If concepts A and B frequently fail together, the edge between them
should carry more weight — indicating a real dependency in the student's mind.
"""
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.concept_edge import ConceptEdge
from app.models.review_log import ReviewLog
from app.models.propagation_log import PropagationLog
from app.algorithms.knowledge_graph import GraphManager, WeightConfig, DEFAULT_CONFIG


# Reviews within this window are considered part of the same study session
SESSION_WINDOW_MINUTES = 30


class SessionTracker:
    """
    Tracks co-review and co-failure patterns between connected concepts
    within a session window. Updates w_data on edges accordingly.
    """

    @classmethod
    def update_co_signals(
        cls,
        db: Session,
        user_id: int,
        concept_id: int,
        rating: int,
        config: WeightConfig = None
    ):
        """
        After a concept is reviewed, check if any connected neighbors were also
        reviewed recently (within SESSION_WINDOW). If so, update co-review and
        co-failure counts on the connecting edges.

        Args:
            db: Database session
            user_id: Current user
            concept_id: The concept that was just reviewed
            rating: The review rating (1=Again, 2=Hard, 3=Good, 4=Easy)
            config: Weight configuration
        """
        if config is None:
            config = DEFAULT_CONFIG

        # Get all edges where this concept is the source
        edges = GraphManager.get_neighbors(db, concept_id, user_id, config)
        if not edges:
            return

        # Define session window
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=SESSION_WINDOW_MINUTES)

        for edge in edges:
            neighbor_id = edge.target_concept_id

            # Check if the neighbor was reviewed in the same session window
            neighbor_review = (
                db.query(ReviewLog)
                .filter(
                    ReviewLog.concept_id == neighbor_id,
                    ReviewLog.user_id == user_id,
                    ReviewLog.reviewed_at >= window_start,
                )
                .order_by(ReviewLog.reviewed_at.desc())
                .first()
            )

            if not neighbor_review:
                continue  # Neighbor wasn't reviewed in this session

            # ── Co-Review detected ────────────────────────────────────────
            edge.co_review_count += 1

            # Also update the reverse edge to keep counts symmetric
            reverse_edge = GraphManager.get_edge(db, user_id, neighbor_id, concept_id)
            if reverse_edge:
                reverse_edge.co_review_count += 1

            # ── Co-Failure check ──────────────────────────────────────────
            # Current concept failed AND neighbor also failed in this session
            current_failed = (rating == 1)
            neighbor_failed = (not neighbor_review.was_correct)

            if current_failed and neighbor_failed:
                edge.co_fail_count += 1
                if reverse_edge:
                    reverse_edge.co_fail_count += 1

                # Log co-failure event
                log = PropagationLog(
                    user_id=user_id,
                    source_concept_id=concept_id,
                    target_concept_id=neighbor_id,
                    event_type="co_failure",
                    delta_stability=0.0,
                    w_final_used=edge.w_final,
                    details=json.dumps({
                        "co_review_count": edge.co_review_count,
                        "co_fail_count": edge.co_fail_count,
                        "current_rating": rating,
                        "neighbor_was_correct": neighbor_review.was_correct,
                    }),
                )
                db.add(log)

            # ── Recalculate w_data ────────────────────────────────────────
            # w_data = co_fail_count / co_review_count
            if edge.co_review_count > 0:
                edge.w_data = round(edge.co_fail_count / edge.co_review_count, 6)
                edge.w_data = GraphManager.clamp(edge.w_data)

            if reverse_edge and reverse_edge.co_review_count > 0:
                reverse_edge.w_data = round(
                    reverse_edge.co_fail_count / reverse_edge.co_review_count, 6
                )
                reverse_edge.w_data = GraphManager.clamp(reverse_edge.w_data)

            # ── Recalculate w_final after w_data changed ──────────────────
            old_w_final = edge.w_final
            GraphManager.update_edge_w_final(edge, config)
            if reverse_edge:
                GraphManager.update_edge_w_final(reverse_edge, config)

            # Log weight evolution if w_final actually changed
            if abs(edge.w_final - old_w_final) > 0.0001:
                weight_log = PropagationLog(
                    user_id=user_id,
                    source_concept_id=concept_id,
                    target_concept_id=neighbor_id,
                    event_type="weight_update",
                    delta_stability=0.0,
                    w_final_used=edge.w_final,
                    details=json.dumps({
                        "old_w_final": round(old_w_final, 6),
                        "new_w_final": round(edge.w_final, 6),
                        "w_expert": edge.w_expert,
                        "w_data": edge.w_data,
                        "w_semantic": edge.w_semantic,
                    }),
                )
                db.add(weight_log)

        db.flush()

        # Re-normalize after potential weight changes
        GraphManager.normalize_outgoing_weights(db, concept_id, user_id, config)
