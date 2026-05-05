"""
routers/graph.py — Knowledge Graph management API.
Provides endpoints for managing concept edges, viewing the full graph,
and inspecting propagation logs.

Endpoints:
  POST   /graph/edges                     — Create an edge between two concepts
  DELETE /graph/edges                     — Remove an edge
  GET    /graph/edges/{concept_id}        — Get all edges for a concept
  GET    /graph/neighbors/{concept_id}    — Get neighbor concepts with weights
  GET    /graph/full                      — Export the full knowledge graph
  GET    /graph/logs/{concept_id}         — Get propagation history
  PUT    /graph/edges/{edge_id}/weight    — Update expert weight on an edge
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.user import User
from app.models.concept import Concept
from app.models.concept_edge import ConceptEdge
from app.models.scheduling import SchedulingData
from app.models.propagation_log import PropagationLog
from app.models.subject import Subject
from app.schemas.graph import (
    EdgeCreate, EdgeDelete, EdgeWeightUpdate,
    EdgeOut, GraphNodeOut, GraphFullOut, PropagationLogOut,
)
from app.algorithms.knowledge_graph import GraphManager
from app.utils.auth import get_current_user
from app.utils.exceptions import not_found, bad_request

router = APIRouter()


# ══════════════════════════════════════════════════════════════════════════════
# Edge CRUD
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/edges", response_model=EdgeOut, status_code=status.HTTP_201_CREATED)
def create_edge(
    payload: EdgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a bidirectional edge between two concepts in the knowledge graph.
    Both concepts must belong to the current user.
    Max 5 neighbors per node is enforced.
    """
    # Validate both concepts exist and belong to user
    source = db.query(Concept).filter(
        Concept.id == payload.source_concept_id,
        Concept.user_id == current_user.id,
    ).first()
    if not source:
        raise not_found("Source concept")

    target = db.query(Concept).filter(
        Concept.id == payload.target_concept_id,
        Concept.user_id == current_user.id,
    ).first()
    if not target:
        raise not_found("Target concept")

    try:
        edge = GraphManager.add_edge(
            db=db,
            user_id=current_user.id,
            source_id=payload.source_concept_id,
            target_id=payload.target_concept_id,
            w_expert=payload.w_expert,
        )
        db.commit()
        db.refresh(edge)
    except ValueError as e:
        raise bad_request(str(e))

    return _edge_to_out(edge, source.title, target.title)


@router.delete("/edges", status_code=status.HTTP_204_NO_CONTENT)
def delete_edge(
    payload: EdgeDelete,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove a bidirectional edge between two concepts."""
    deleted = GraphManager.remove_edge(
        db=db,
        user_id=current_user.id,
        source_id=payload.source_concept_id,
        target_id=payload.target_concept_id,
    )
    if not deleted:
        raise not_found("Edge")
    db.commit()


@router.put("/edges/{edge_id}/weight", response_model=EdgeOut)
def update_edge_weight(
    edge_id: int,
    payload: EdgeWeightUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the expert weight on an existing edge."""
    edge = db.query(ConceptEdge).filter(
        ConceptEdge.id == edge_id,
        ConceptEdge.user_id == current_user.id,
    ).first()
    if not edge:
        raise not_found("Edge")

    updated_edge = GraphManager.update_expert_weight(
        db=db,
        user_id=current_user.id,
        source_id=edge.source_concept_id,
        target_id=edge.target_concept_id,
        new_w_expert=payload.w_expert,
    )
    db.commit()
    db.refresh(updated_edge)

    source_title = _get_concept_title(db, edge.source_concept_id)
    target_title = _get_concept_title(db, edge.target_concept_id)
    return _edge_to_out(updated_edge, source_title, target_title)


# ══════════════════════════════════════════════════════════════════════════════
# Graph Queries
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/edges/{concept_id}", response_model=List[EdgeOut])
def get_concept_edges(
    concept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all outgoing edges for a specific concept."""
    edges = GraphManager.get_neighbors(db, concept_id, current_user.id)
    result = []
    for edge in edges:
        source_title = _get_concept_title(db, edge.source_concept_id)
        target_title = _get_concept_title(db, edge.target_concept_id)
        result.append(_edge_to_out(edge, source_title, target_title))
    return result


@router.get("/neighbors/{concept_id}", response_model=List[GraphNodeOut])
def get_neighbors(
    concept_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all neighbor concept nodes with their scheduling state."""
    edges = GraphManager.get_neighbors(db, concept_id, current_user.id)
    result = []
    for edge in edges:
        concept = db.query(Concept).filter(Concept.id == edge.target_concept_id).first()
        if not concept:
            continue
        sched = db.query(SchedulingData).filter(
            SchedulingData.concept_id == concept.id,
            SchedulingData.user_id == current_user.id,
        ).first()
        if not sched:
            continue
        neighbor_count = GraphManager.count_outgoing(db, concept.id, current_user.id)
        subject = db.query(Subject).filter(Subject.id == concept.subject_id).first()
        result.append(GraphNodeOut(
            concept_id=concept.id,
            title=concept.title,
            subject_name=subject.name if subject else "",
            stability=sched.stability,
            difficulty=sched.difficulty_fsrs,
            retrievability=sched.retrievability,
            interval_days=sched.interval_days,
            neighbor_count=neighbor_count,
        ))
    return result


@router.get("/full", response_model=GraphFullOut)
def get_full_graph(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export the full knowledge graph for the current user.
    Returns all concept nodes (with scheduling state) and all edges.
    """
    # Get all concepts with their scheduling data
    concepts = db.query(Concept).filter(Concept.user_id == current_user.id).all()
    nodes = []
    for concept in concepts:
        sched = db.query(SchedulingData).filter(
            SchedulingData.concept_id == concept.id,
            SchedulingData.user_id == current_user.id,
        ).first()
        neighbor_count = GraphManager.count_outgoing(db, concept.id, current_user.id)
        subject = db.query(Subject).filter(Subject.id == concept.subject_id).first()
        nodes.append(GraphNodeOut(
            concept_id=concept.id,
            title=concept.title,
            subject_name=subject.name if subject else "",
            stability=sched.stability if sched else 0.0,
            difficulty=sched.difficulty_fsrs if sched else 5.0,
            retrievability=sched.retrievability if sched else 1.0,
            interval_days=sched.interval_days if sched else 1,
            neighbor_count=neighbor_count,
        ))

    # Get all edges
    all_edges = GraphManager.get_all_edges(db, current_user.id)
    edge_outs = []
    for edge in all_edges:
        source_title = _get_concept_title(db, edge.source_concept_id)
        target_title = _get_concept_title(db, edge.target_concept_id)
        edge_outs.append(_edge_to_out(edge, source_title, target_title))

    return GraphFullOut(
        nodes=nodes,
        edges=edge_outs,
        total_nodes=len(nodes),
        total_edges=len(edge_outs),
    )


# ══════════════════════════════════════════════════════════════════════════════
# Propagation Logs
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/logs/{concept_id}", response_model=List[PropagationLogOut])
def get_propagation_logs(
    concept_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get propagation event history for a concept.
    Shows both events WHERE this concept was the source and the target.
    """
    logs = (
        db.query(PropagationLog)
        .filter(
            PropagationLog.user_id == current_user.id,
            (
                (PropagationLog.source_concept_id == concept_id) |
                (PropagationLog.target_concept_id == concept_id)
            ),
        )
        .order_by(PropagationLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return logs


# ══════════════════════════════════════════════════════════════════════════════
# Helper Functions
# ══════════════════════════════════════════════════════════════════════════════

def _get_concept_title(db: Session, concept_id: int) -> str:
    """Get a concept's title by ID."""
    concept = db.query(Concept).filter(Concept.id == concept_id).first()
    return concept.title if concept else f"Concept #{concept_id}"


def _edge_to_out(edge: ConceptEdge, source_title: str, target_title: str) -> EdgeOut:
    """Convert a ConceptEdge ORM object to an EdgeOut schema."""
    return EdgeOut(
        id=edge.id,
        source_concept_id=edge.source_concept_id,
        target_concept_id=edge.target_concept_id,
        source_title=source_title,
        target_title=target_title,
        w_expert=edge.w_expert,
        w_data=edge.w_data,
        w_semantic=edge.w_semantic,
        w_final=edge.w_final,
        co_review_count=edge.co_review_count,
        co_fail_count=edge.co_fail_count,
        created_at=edge.created_at,
        updated_at=edge.updated_at,
    )
