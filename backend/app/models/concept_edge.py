"""
models/concept_edge.py — ConceptEdge ORM model.
Represents a weighted, directed edge between two concept nodes in the
knowledge graph. Each edge carries multi-signal weights:
  - w_expert:   manually set by the user or heuristically derived (0-1)
  - w_data:     learned from co-failure patterns during study sessions (0-1)
  - w_semantic: placeholder for future embedding-based cosine similarity (0-1)
  - w_final:    combined weight = α*w_expert + β*w_data + γ*w_semantic

Also tracks co-review and co-failure counts used to compute w_data.
"""
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class ConceptEdge(Base):
    __tablename__ = "concept_edges"

    # Ensure no duplicate edges for the same user between the same pair of concepts
    __table_args__ = (
        UniqueConstraint("user_id", "source_concept_id", "target_concept_id",
                         name="uq_user_source_target"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source_concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)
    target_concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)

    # ── Multi-Signal Weights ──────────────────────────────────────────────────
    w_expert = Column(Float, default=0.5)       # Manual / heuristic weight
    w_data = Column(Float, default=0.0)         # Learned from co-failure patterns
    w_semantic = Column(Float, default=0.0)     # Placeholder: embedding cosine sim

    # Combined weight: α*w_expert + β*w_data + γ*w_semantic
    # Default: 0.7*0.5 + 0.3*0.0 + 0.0*0.0 = 0.35
    w_final = Column(Float, default=0.35)

    # ── Data-Driven Signal Tracking ───────────────────────────────────────────
    co_review_count = Column(Integer, default=0)    # Both reviewed in same session
    co_fail_count = Column(Integer, default=0)      # Both FAILED in same session

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user = relationship("User")
    source_concept = relationship("Concept", foreign_keys=[source_concept_id])
    target_concept = relationship("Concept", foreign_keys=[target_concept_id])
