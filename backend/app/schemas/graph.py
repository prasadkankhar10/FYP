"""
schemas/graph.py — Pydantic schemas for Knowledge Graph API endpoints.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ══════════════════════════════════════════════════════════════════════════════
# Request Schemas
# ══════════════════════════════════════════════════════════════════════════════

class EdgeCreate(BaseModel):
    """Create a bidirectional edge between two concepts."""
    source_concept_id: int
    target_concept_id: int
    w_expert: float = Field(default=0.5, ge=0.0, le=1.0, description="Expert weight (0-1)")


class EdgeDelete(BaseModel):
    """Remove an edge between two concepts."""
    source_concept_id: int
    target_concept_id: int


class EdgeWeightUpdate(BaseModel):
    """Update the expert weight on an existing edge."""
    w_expert: float = Field(ge=0.0, le=1.0, description="New expert weight (0-1)")


# ══════════════════════════════════════════════════════════════════════════════
# Response Schemas
# ══════════════════════════════════════════════════════════════════════════════

class EdgeOut(BaseModel):
    """Full edge representation with all weight signals."""
    id: int
    source_concept_id: int
    target_concept_id: int
    source_title: Optional[str] = None
    target_title: Optional[str] = None
    w_expert: float
    w_data: float
    w_semantic: float
    w_final: float
    co_review_count: int
    co_fail_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GraphNodeOut(BaseModel):
    """A concept node with its scheduling state and neighbor count."""
    concept_id: int
    title: str
    subject_name: Optional[str] = None
    stability: float
    difficulty: float
    retrievability: float
    interval_days: int
    neighbor_count: int

    model_config = {"from_attributes": True}


class GraphFullOut(BaseModel):
    """Full graph export: all nodes and edges for the current user."""
    nodes: List[GraphNodeOut]
    edges: List[EdgeOut]
    total_nodes: int
    total_edges: int


class PropagationLogOut(BaseModel):
    """A single propagation event from the audit trail."""
    id: int
    source_concept_id: int
    target_concept_id: int
    event_type: str
    delta_stability: float
    w_final_used: float
    details: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
