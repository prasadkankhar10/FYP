"""
algorithms/knowledge_graph.py — Knowledge Graph Manager.
Pure graph operations layer: CRUD for edges, weight computation, and normalization.
This module contains NO FSRS math — it is purely a graph abstraction.

Architecture:
  - WeightConfig: holds the α, β, γ mixing coefficients and propagation limits
  - GraphManager: stateless utility class for all graph operations

Design decisions:
  - Max 5 neighbors per node to keep propagation bounded
  - All weights clamped to [0, 1]
  - Sum of outgoing w_final normalized to ≤ 1.0
  - Edges are bidirectional: adding A→B also adds B→A
"""
from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.concept_edge import ConceptEdge


# ══════════════════════════════════════════════════════════════════════════════
# Configuration
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class WeightConfig:
    """
    Mixing coefficients for the multi-signal weight formula:
        w_final = α * w_expert + β * w_data + γ * w_semantic

    Also holds propagation limits used by the propagation engine.
    """
    alpha: float = 0.5      # Expert weight contribution
    beta: float = 0.3       # Data-driven weight contribution
    gamma: float = 0.2      # Semantic weight contribution

    # Propagation limits
    max_neighbors: int = 5               # Max edges per node
    propagation_factor_fail: float = 0.15    # How much of ΔS to propagate on failure
    propagation_factor_pass: float = 0.05    # How much of ΔS to propagate on success
    propagation_factor_cap: float = 0.20     # Hard cap on propagation factor
    stability_floor: float = 0.4             # Minimum stability after propagation


# Global default config — can be overridden per-user in the future
DEFAULT_CONFIG = WeightConfig()


# ══════════════════════════════════════════════════════════════════════════════
# Graph Manager
# ══════════════════════════════════════════════════════════════════════════════

class GraphManager:
    """
    Stateless utility class for knowledge graph operations.
    All methods are classmethods — no instance state needed.
    """

    @staticmethod
    def clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Clamp a value to [min_val, max_val]."""
        return max(min_val, min(max_val, value))

    @classmethod
    def compute_w_final(cls, edge: ConceptEdge, config: WeightConfig = None) -> float:
        """
        Compute the combined final weight for an edge.
        Formula: w_final = α * w_expert + β * w_data + γ * w_semantic
        """
        if config is None:
            config = DEFAULT_CONFIG

        raw = (config.alpha * edge.w_expert +
               config.beta * edge.w_data +
               config.gamma * edge.w_semantic)
        return cls.clamp(raw)

    @classmethod
    def get_neighbors(
        cls,
        db: Session,
        concept_id: int,
        user_id: int,
        config: WeightConfig = None
    ) -> List[ConceptEdge]:
        """
        Get all outgoing edges from a concept (1-hop neighbors).
        Returns at most max_neighbors edges, ordered by w_final descending
        so the strongest connections are prioritized.
        """
        if config is None:
            config = DEFAULT_CONFIG

        edges = (
            db.query(ConceptEdge)
            .filter(
                ConceptEdge.source_concept_id == concept_id,
                ConceptEdge.user_id == user_id,
            )
            .order_by(ConceptEdge.w_final.desc())
            .limit(config.max_neighbors)
            .all()
        )
        return edges

    @classmethod
    def get_all_edges(cls, db: Session, user_id: int) -> List[ConceptEdge]:
        """Get ALL edges for a user (used for full graph export)."""
        return (
            db.query(ConceptEdge)
            .filter(ConceptEdge.user_id == user_id)
            .all()
        )

    @classmethod
    def get_edge(
        cls,
        db: Session,
        user_id: int,
        source_id: int,
        target_id: int
    ) -> Optional[ConceptEdge]:
        """Get a specific edge between two concepts."""
        return (
            db.query(ConceptEdge)
            .filter(
                ConceptEdge.user_id == user_id,
                ConceptEdge.source_concept_id == source_id,
                ConceptEdge.target_concept_id == target_id,
            )
            .first()
        )

    @classmethod
    def count_outgoing(cls, db: Session, concept_id: int, user_id: int) -> int:
        """Count outgoing edges from a concept."""
        return (
            db.query(ConceptEdge)
            .filter(
                ConceptEdge.source_concept_id == concept_id,
                ConceptEdge.user_id == user_id,
            )
            .count()
        )

    @classmethod
    def add_edge(
        cls,
        db: Session,
        user_id: int,
        source_id: int,
        target_id: int,
        w_expert: float = 0.5,
        config: WeightConfig = None,
    ) -> ConceptEdge:
        """
        Create a bidirectional edge between two concepts.
        Enforces:
          - No self-loops
          - Max 5 neighbors per node
          - No duplicate edges
          - Weight clamping
          - Calculates w_semantic via cosine similarity

        Returns the source→target edge (the "forward" direction).
        """
        from app.models.concept import Concept
        from app.utils.embeddings import compute_similarity
        if config is None:
            config = DEFAULT_CONFIG

        if source_id == target_id:
            raise ValueError("Cannot create a self-loop edge.")

        # Check neighbor limits for both sides
        if cls.count_outgoing(db, source_id, user_id) >= config.max_neighbors:
            raise ValueError(
                f"Concept {source_id} already has {config.max_neighbors} neighbors (max)."
            )
        if cls.count_outgoing(db, target_id, user_id) >= config.max_neighbors:
            raise ValueError(
                f"Concept {target_id} already has {config.max_neighbors} neighbors (max)."
            )

        # Check for existing edge
        existing = cls.get_edge(db, user_id, source_id, target_id)
        if existing:
            raise ValueError(
                f"Edge already exists between {source_id} → {target_id}."
            )

        w_expert = cls.clamp(w_expert)

        # Compute semantic similarity
        source_concept = db.query(Concept).filter(Concept.id == source_id).first()
        target_concept = db.query(Concept).filter(Concept.id == target_id).first()
        
        w_semantic = 0.0
        if source_concept and target_concept:
            # Combine title and content for embedding
            text1 = f"{source_concept.title} {source_concept.content or ''}"
            text2 = f"{target_concept.title} {target_concept.content or ''}"
            w_semantic = compute_similarity(text1, text2)

        # Create forward edge: source → target
        forward = ConceptEdge(
            user_id=user_id,
            source_concept_id=source_id,
            target_concept_id=target_id,
            w_expert=w_expert,
            w_data=0.0,
            w_semantic=w_semantic,
        )
        forward.w_final = cls.compute_w_final(forward, config)
        db.add(forward)

        # Create reverse edge: target → source (same expert weight)
        reverse_existing = cls.get_edge(db, user_id, target_id, source_id)
        if not reverse_existing:
            reverse = ConceptEdge(
                user_id=user_id,
                source_concept_id=target_id,
                target_concept_id=source_id,
                w_expert=w_expert,
                w_data=0.0,
                w_semantic=w_semantic,
            )
            reverse.w_final = cls.compute_w_final(reverse, config)
            db.add(reverse)

        db.flush()

        # Normalize weights after adding new edges
        cls.normalize_outgoing_weights(db, source_id, user_id, config)
        cls.normalize_outgoing_weights(db, target_id, user_id, config)

        return forward

    @classmethod
    def remove_edge(
        cls,
        db: Session,
        user_id: int,
        source_id: int,
        target_id: int
    ) -> bool:
        """
        Remove a bidirectional edge between two concepts.
        Returns True if edges were found and deleted.
        """
        deleted = False

        forward = cls.get_edge(db, user_id, source_id, target_id)
        if forward:
            db.delete(forward)
            deleted = True

        reverse = cls.get_edge(db, user_id, target_id, source_id)
        if reverse:
            db.delete(reverse)
            deleted = True

        if deleted:
            db.flush()

        return deleted

    @classmethod
    def update_edge_w_final(
        cls,
        edge: ConceptEdge,
        config: WeightConfig = None
    ) -> float:
        """Recalculate and set w_final on an edge. Returns new w_final."""
        new_w_final = cls.compute_w_final(edge, config)
        edge.w_final = new_w_final
        return new_w_final

    @classmethod
    def normalize_outgoing_weights(
        cls,
        db: Session,
        concept_id: int,
        user_id: int,
        config: WeightConfig = None
    ):
        """
        Normalize outgoing w_final values so their sum ≤ 1.0.
        If the sum exceeds 1.0, scale all weights proportionally.
        This prevents propagation explosion from high-degree nodes.
        """
        edges = cls.get_neighbors(db, concept_id, user_id, config)
        if not edges:
            return

        total = sum(e.w_final for e in edges)
        if total <= 1.0:
            return  # Already within budget

        # Scale down proportionally
        scale = 1.0 / total
        for edge in edges:
            edge.w_final = round(cls.clamp(edge.w_final * scale), 6)

        db.flush()

    @classmethod
    def update_expert_weight(
        cls,
        db: Session,
        user_id: int,
        source_id: int,
        target_id: int,
        new_w_expert: float,
        config: WeightConfig = None
    ) -> Optional[ConceptEdge]:
        """
        Update the expert weight on an edge and recalculate w_final.
        Also updates the reverse edge to keep weights symmetric.
        """
        if config is None:
            config = DEFAULT_CONFIG

        edge = cls.get_edge(db, user_id, source_id, target_id)
        if not edge:
            return None

        edge.w_expert = cls.clamp(new_w_expert)
        cls.update_edge_w_final(edge, config)

        # Keep reverse edge in sync
        reverse = cls.get_edge(db, user_id, target_id, source_id)
        if reverse:
            reverse.w_expert = edge.w_expert
            cls.update_edge_w_final(reverse, config)

        db.flush()

        # Re-normalize after weight change
        cls.normalize_outgoing_weights(db, source_id, user_id, config)
        cls.normalize_outgoing_weights(db, target_id, user_id, config)

        return edge
