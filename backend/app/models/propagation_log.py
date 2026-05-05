"""
models/propagation_log.py — PropagationLog ORM model.
Append-only audit trail for every stability propagation event and weight
update in the knowledge graph. This is the primary data source for:
  - Debugging propagation behavior
  - Visualizing weight evolution over time
  - Validating that the system is not exploding
"""
from sqlalchemy import Column, Integer, Float, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class PropagationLog(Base):
    __tablename__ = "propagation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    target_concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)

    # Type of event logged
    # Values: "positive_propagation" | "negative_propagation" | "weight_update" | "co_failure"
    event_type = Column(String(50), nullable=False)

    # The stability delta applied to the target concept
    delta_stability = Column(Float, default=0.0)

    # The w_final value at the time of propagation (snapshot for audit)
    w_final_used = Column(Float, default=0.0)

    # JSON string with additional context (old/new weights, ratings, etc.)
    details = Column(Text, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # ── Relationships ─────────────────────────────────────────────────────────
    user = relationship("User")
    source_concept = relationship("Concept", foreign_keys=[source_concept_id])
    target_concept = relationship("Concept", foreign_keys=[target_concept_id])
