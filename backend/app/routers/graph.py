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
import json

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
            subject_id=concept.subject_id,
            title=concept.title,
            content=concept.content,
            difficulty_level=concept.difficulty,
            parent_concept_id=concept.parent_concept_id,
            subject_name=subject.name if subject else "",
            stability=sched.stability,
            difficulty=sched.difficulty_fsrs,
            retrievability=sched.retrievability,
            interval_days=sched.interval_days,
            algorithm=sched.algorithm,
            repetitions=sched.repetitions,
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
            subject_id=concept.subject_id,
            title=concept.title,
            content=concept.content,
            difficulty_level=concept.difficulty,
            parent_concept_id=concept.parent_concept_id,
            subject_name=subject.name if subject else "",
            stability=sched.stability if sched else 0.0,
            difficulty=sched.difficulty_fsrs if sched else 5.0,
            retrievability=sched.retrievability if sched else 1.0,
            interval_days=sched.interval_days if sched else 1,
            algorithm=sched.algorithm if sched else "fsrs",
            repetitions=sched.repetitions if sched else 0,
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
# Weight Tuning
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/tune-weights")
def tune_weights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Compute a simple heuristic to adjust Knowledge Graph mixing weights (α, β, γ).
    As the user performs more reviews, the data-driven weight (β) should increase.
    """
    from app.models.review_log import ReviewLog
    from app.algorithms.knowledge_graph import WeightConfig

    review_count = db.query(ReviewLog).filter(ReviewLog.user_id == current_user.id).count()

    # Heuristic:
    # Base: α=0.5, β=0.3, γ=0.2
    # For every 100 reviews, β increases by 0.05, α decreases by 0.05 (clamped)
    
    beta_shift = min(0.4, (review_count // 100) * 0.05)
    
    new_alpha = max(0.1, 0.5 - beta_shift)
    new_beta = min(0.7, 0.3 + beta_shift)
    new_gamma = 1.0 - new_alpha - new_beta

    new_params = {
        "alpha": round(new_alpha, 2),
        "beta": round(new_beta, 2),
        "gamma": round(new_gamma, 2),
    }

    current_user.kg_params = json.dumps(new_params)
    db.commit()

    # Apply new weights to all existing edges
    config = WeightConfig(alpha=new_alpha, beta=new_beta, gamma=new_gamma)
    all_edges = GraphManager.get_all_edges(db, current_user.id)
    for edge in all_edges:
        GraphManager.update_edge_w_final(edge, config)
    
    db.commit()

    return {
        "success": True,
        "message": f"KG weights tuned based on {review_count} reviews.",
        "params": new_params
    }


@router.post("/connect-all")
def connect_all_concepts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Synthesizes and connects all concepts for the current user into a cohesive neural graph.
    Uses semantic similarity and hierarchical topic mapping to link related concepts together.
    """
    concepts = db.query(Concept).filter(Concept.user_id == current_user.id).all()
    if len(concepts) < 2:
        return {
            "success": True,
            "connections_created": 0,
            "total_edges": 0,
            "message": "Need at least 2 concepts to build neural connections."
        }

    from app.utils.embeddings import compute_similarity

    # Pre-build text representations
    texts = {c.id: f"{c.title}: {c.content or ''}" for c in concepts}

    edges_created = 0
    for i, c1 in enumerate(concepts):
        existing_neighbors = {e.target_concept_id for e in GraphManager.get_neighbors(db, c1.id, current_user.id)}
        
        # Candidate ranking based on semantic similarity + subject proximity
        scored_candidates = []
        for c2 in concepts:
            if c1.id == c2.id or c2.id in existing_neighbors:
                continue
            sim = compute_similarity(texts[c1.id], texts[c2.id])
            # Give a slight boost if same subject, but allow cross-subject connections
            subject_boost = 0.15 if c1.subject_id == c2.subject_id else 0.05
            scored_candidates.append((c2, sim + subject_boost))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        top_candidates = [c for c, score in scored_candidates[:4]]

        for c2 in top_candidates:
            if c2.id not in existing_neighbors:
                if GraphManager.count_outgoing(db, c1.id, current_user.id) < 5 and GraphManager.count_outgoing(db, c2.id, current_user.id) < 5:
                    try:
                        GraphManager.add_edge(
                            db=db,
                            user_id=current_user.id,
                            source_id=c1.id,
                            target_id=c2.id,
                            w_expert=0.6
                        )
                        if not c2.parent_concept_id and c1.id != c2.id:
                            c2.parent_concept_id = c1.id
                        edges_created += 1
                    except Exception:
                        pass

    db.commit()
    total_edges = db.query(ConceptEdge).filter(ConceptEdge.user_id == current_user.id).count()
    return {
        "success": True,
        "connections_created": edges_created,
        "total_edges": total_edges,
        "message": f"Successfully connected all concepts! Synthesized {edges_created} new neural synapses."
    }


@router.get("/config")
def get_graph_config(
    current_user: User = Depends(get_current_user),
):
    """Get the current graph config parameters."""
    from app.algorithms.knowledge_graph import DEFAULT_CONFIG
    
    params = {
        "alpha": DEFAULT_CONFIG.alpha,
        "beta": DEFAULT_CONFIG.beta,
        "gamma": DEFAULT_CONFIG.gamma,
        "propagation_factor_fail": DEFAULT_CONFIG.propagation_factor_fail,
        "propagation_factor_pass": DEFAULT_CONFIG.propagation_factor_pass,
    }
    
    if current_user.kg_params:
        try:
            user_params = json.loads(current_user.kg_params)
            params.update(user_params)
        except json.JSONDecodeError:
            pass
            
    return params


from pydantic import BaseModel
class ConfigUpdate(BaseModel):
    alpha: float
    beta: float
    gamma: float
    propagation_factor_fail: float
    propagation_factor_pass: float


@router.put("/config")
def update_graph_config(
    payload: ConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually update the graph config parameters (for research dashboard)."""
    from app.algorithms.knowledge_graph import WeightConfig
    
    new_params = {
        "alpha": payload.alpha,
        "beta": payload.beta,
        "gamma": payload.gamma,
        "propagation_factor_fail": payload.propagation_factor_fail,
        "propagation_factor_pass": payload.propagation_factor_pass,
    }
    
    current_user.kg_params = json.dumps(new_params)
    db.commit()

    # Apply new weights to all existing edges
    config = WeightConfig(
        alpha=payload.alpha, 
        beta=payload.beta, 
        gamma=payload.gamma,
        propagation_factor_fail=payload.propagation_factor_fail,
        propagation_factor_pass=payload.propagation_factor_pass
    )
    
    all_edges = GraphManager.get_all_edges(db, current_user.id)
    for edge in all_edges:
        GraphManager.update_edge_w_final(edge, config)
    
    db.commit()

    return {"success": True, "params": new_params}



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
