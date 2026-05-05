"""
demo_simulation.py — Standalone simulation of the Multi-Concept FSRS Knowledge Graph.
Runs entirely in-memory (no database required) to demonstrate:

  1. Standard FSRS vs Graph-aware FSRS stability evolution
  2. Propagation of stability changes to neighbors
  3. Co-failure data signal learning (w_data evolution)
  4. Scheduling interval adjustment based on graph health
  5. Weight normalization

Usage:
    cd backend
    python demo_simulation.py
"""
import math
import sys
import os
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# Add the backend directory to path so we can import the algorithm modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ══════════════════════════════════════════════════════════════════════════════
# In-Memory Data Structures (no database needed)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class SimConcept:
    """A concept node in the simulation."""
    id: int
    title: str
    stability: float = 0.0
    difficulty: float = 5.0
    retrievability: float = 1.0
    interval_days: int = 1
    repetitions: int = 0
    ease_factor: float = 2.5

    # History tracking
    stability_history: list = field(default_factory=list)


@dataclass
class SimEdge:
    """An edge between two concept nodes."""
    source_id: int
    target_id: int
    w_expert: float = 0.5
    w_data: float = 0.0
    w_semantic: float = 0.0
    w_final: float = 0.35
    co_review_count: int = 0
    co_fail_count: int = 0


@dataclass
class SimPropEvent:
    """A propagation event log entry."""
    step: int
    source_id: int
    target_id: int
    event_type: str
    delta_stability: float
    w_final_used: float


# ══════════════════════════════════════════════════════════════════════════════
# Configuration (mirrors knowledge_graph.py)
# ══════════════════════════════════════════════════════════════════════════════

ALPHA = 0.7
BETA = 0.3
GAMMA = 0.0
PROP_FACTOR_FAIL = 0.15
PROP_FACTOR_PASS = 0.05
STABILITY_FLOOR = 0.4


# ══════════════════════════════════════════════════════════════════════════════
# FSRS v4 core math (copied from fsrs.py to keep simulation standalone)
# ══════════════════════════════════════════════════════════════════════════════

FSRS_WEIGHTS = [
    0.40255, 1.18385, 3.173, 15.69105, 7.1949, 0.5345, 1.4604, 0.0046,
    1.54575, 0.1192, 1.01925, 1.9395, 0.11, 0.29605, 2.2698, 0.2315, 2.9898
]


def fsrs_calculate(concept: SimConcept, rating: int) -> Tuple[float, float, float]:
    """
    Run standard FSRS math. Returns (new_S, new_D, R).
    """
    w = FSRS_WEIGHTS
    last_D = concept.difficulty if concept.difficulty > 0 else 5.0
    last_S = concept.stability
    interval = concept.interval_days

    # Retrievability
    R = 1.0
    if last_S > 0:
        R = math.pow(1 + interval / (9 * last_S), -1)

    if last_S == 0:
        S = w[{1: 0, 2: 1, 3: 2, 4: 3}[rating]]
        D = w[4] - w[5] * (rating - 3)
    else:
        D = last_D - w[6] * (rating - 3)
        D = D * (1 - w[7]) + w[4] * w[7]
        D = min(max(D, 1.0), 10.0)

        if rating == 1:
            S = w[11] * math.pow(last_D, -w[12]) * (math.pow(last_S + 1, w[13]) - 1) * math.exp(w[14] * (1 - R))
        else:
            S = last_S * (1 + math.exp(w[8]) * (11 - last_D) * math.pow(last_S, -w[9]) * (math.exp((1 - R) * w[10]) - 1))
            if rating == 2:
                S *= w[15]
            elif rating == 4:
                S *= w[16]

    return round(S, 4), round(D, 4), round(R, 4)


# ══════════════════════════════════════════════════════════════════════════════
# Graph Operations
# ══════════════════════════════════════════════════════════════════════════════

def compute_w_final(edge: SimEdge) -> float:
    """w_final = α*w_expert + β*w_data + γ*w_semantic, clamped [0,1]."""
    raw = ALPHA * edge.w_expert + BETA * edge.w_data + GAMMA * edge.w_semantic
    return max(0.0, min(1.0, raw))


def normalize_outgoing(edges: List[SimEdge], concept_id: int):
    """Normalize outgoing w_final from a concept so sum ≤ 1.0."""
    outgoing = [e for e in edges if e.source_id == concept_id]
    total = sum(e.w_final for e in outgoing)
    if total <= 1.0:
        return
    scale = 1.0 / total
    for e in outgoing:
        e.w_final = round(e.w_final * scale, 6)


def propagate(
    concepts: Dict[int, SimConcept],
    edges: List[SimEdge],
    source_id: int,
    delta_S: float,
    rating: int,
    step: int,
    events: List[SimPropEvent],
):
    """Propagate ΔS to 1-hop neighbors."""
    if rating == 2:
        return  # No propagation on Hard

    prop_factor = PROP_FACTOR_FAIL if rating == 1 else PROP_FACTOR_PASS

    outgoing = [e for e in edges if e.source_id == source_id]
    for edge in outgoing:
        delta_neighbor = edge.w_final * delta_S * prop_factor
        if abs(delta_neighbor) < 0.001:
            continue

        target = concepts[edge.target_id]
        old_stab = target.stability
        new_stab = max(STABILITY_FLOOR, old_stab + delta_neighbor)
        target.stability = round(new_stab, 4)
        target.interval_days = max(1, round(new_stab))

        event_type = "negative_propagation" if delta_neighbor < 0 else "positive_propagation"
        events.append(SimPropEvent(
            step=step, source_id=source_id, target_id=edge.target_id,
            event_type=event_type, delta_stability=round(delta_neighbor, 6),
            w_final_used=edge.w_final,
        ))


def adjust_interval(interval: int, avg_neighbor_R: float) -> int:
    """Adjust interval based on neighbor health."""
    if avg_neighbor_R >= 1.0:
        return interval
    if avg_neighbor_R < 0.5:
        return max(1, round(interval * 0.85))
    elif avg_neighbor_R > 0.85:
        return max(1, round(interval * 1.10))
    return interval


# ══════════════════════════════════════════════════════════════════════════════
# Simulation Setup
# ══════════════════════════════════════════════════════════════════════════════

def build_example_graph() -> Tuple[Dict[int, SimConcept], List[SimEdge]]:
    """
    Create an example knowledge graph:

        [1] Algebra
         ├── [2] Linear Equations
         │    └── [4] Systems of Equations
         └── [3] Quadratic Equations
              └── [5] Quadratic Formula

    Edges (bidirectional):
      1 ↔ 2 (w_expert=0.7)
      1 ↔ 3 (w_expert=0.6)
      2 ↔ 4 (w_expert=0.8)
      3 ↔ 5 (w_expert=0.7)
    """
    concepts = {
        1: SimConcept(id=1, title="Algebra"),
        2: SimConcept(id=2, title="Linear Equations"),
        3: SimConcept(id=3, title="Quadratic Equations"),
        4: SimConcept(id=4, title="Systems of Equations"),
        5: SimConcept(id=5, title="Quadratic Formula"),
    }

    edge_defs = [
        (1, 2, 0.7), (2, 1, 0.7),
        (1, 3, 0.6), (3, 1, 0.6),
        (2, 4, 0.8), (4, 2, 0.8),
        (3, 5, 0.7), (5, 3, 0.7),
    ]

    edges = []
    for src, tgt, w_exp in edge_defs:
        e = SimEdge(source_id=src, target_id=tgt, w_expert=w_exp)
        e.w_final = compute_w_final(e)
        edges.append(e)

    # Normalize
    for cid in concepts:
        normalize_outgoing(edges, cid)

    return concepts, edges


# ══════════════════════════════════════════════════════════════════════════════
# Simulation Runner
# ══════════════════════════════════════════════════════════════════════════════

def run_simulation():
    """
    Simulate 20 review sessions and compare standard FSRS vs Graph-aware FSRS.
    """
    print("=" * 80)
    print("  MULTI-CONCEPT FSRS — KNOWLEDGE GRAPH SIMULATION")
    print("=" * 80)

    # Build graph
    concepts, edges = build_example_graph()

    # Also create independent copies for baseline (no graph) comparison
    baseline = {cid: SimConcept(id=cid, title=c.title) for cid, c in concepts.items()}

    events: List[SimPropEvent] = []

    # Review schedule: (step, concept_id, rating)
    # Simulates a student who struggles with Quadratics but is good at Linear
    reviews = [
        # Session 1: First reviews
        (1, 1, 3),   # Algebra: Good
        (2, 2, 3),   # Linear Eq: Good
        (3, 3, 3),   # Quadratic Eq: Good
        (4, 4, 3),   # Systems: Good
        (5, 5, 3),   # Quadratic Formula: Good
        # Session 2: Mixed performance
        (6, 1, 4),   # Algebra: Easy
        (7, 2, 3),   # Linear Eq: Good
        (8, 3, 1),   # Quadratic Eq: FAILED ← should propagate to neighbors
        (9, 5, 1),   # Quadratic Formula: FAILED ← co-failure with #3
        (10, 4, 3),  # Systems: Good
        # Session 3: Recovery attempt
        (11, 3, 2),  # Quadratic Eq: Hard (no propagation)
        (12, 5, 3),  # Quadratic Formula: Good (recovered)
        (13, 1, 3),  # Algebra: Good
        # Session 4: Quadratics failing again
        (14, 3, 1),  # Quadratic Eq: FAILED again
        (15, 5, 1),  # Quadratic Formula: FAILED again (co-failure)
        (16, 2, 4),  # Linear Eq: Easy
        (17, 4, 3),  # Systems: Good
        # Session 5: Final review
        (18, 1, 4),  # Algebra: Easy
        (19, 3, 3),  # Quadratic Eq: Good (finally)
        (20, 5, 3),  # Quadratic Formula: Good
    ]

    print("\n📊 REVIEW LOG:")
    print("-" * 80)
    print(f"{'Step':>4} | {'Concept':25s} | {'Rating':6s} | {'S (Base)':>9s} | {'S (Graph)':>10s} | {'ΔS':>8s}")
    print("-" * 80)

    for step, cid, rating in reviews:
        concept = concepts[cid]
        base = baseline[cid]

        # Save old stability for delta
        old_S_graph = concept.stability
        old_S_base = base.stability

        # Run standard FSRS on baseline
        new_S_base, new_D_base, R_base = fsrs_calculate(base, rating)
        base.stability = new_S_base
        base.difficulty = new_D_base
        base.retrievability = R_base
        base.interval_days = max(1, round(new_S_base))
        base.repetitions += 1 if rating > 1 else 0
        base.stability_history.append(new_S_base)

        # Run standard FSRS on graph concept (same math)
        new_S_graph, new_D_graph, R_graph = fsrs_calculate(concept, rating)
        delta_S = new_S_graph - old_S_graph
        concept.stability = new_S_graph
        concept.difficulty = new_D_graph
        concept.retrievability = R_graph
        concept.interval_days = max(1, round(new_S_graph))
        concept.repetitions += 1 if rating > 1 else 0

        # Run propagation (graph-only)
        propagate(concepts, edges, cid, delta_S, rating, step, events)

        # Update co-failure signals (check if neighbor also failed in same "session")
        if rating == 1:
            outgoing = [e for e in edges if e.source_id == cid]
            for edge in outgoing:
                edge.co_review_count += 1
                # Simple check: did we simulate the neighbor failing recently?
                neighbor_reviews = [(s, c, r) for s, c, r in reviews if c == edge.target_id and s <= step and s >= step - 3]
                if any(r == 1 for _, _, r in neighbor_reviews):
                    edge.co_fail_count += 1
                    edge.w_data = round(edge.co_fail_count / edge.co_review_count, 4)
                    edge.w_final = compute_w_final(edge)

        # Adjust interval based on neighbor health
        outgoing = [e for e in edges if e.source_id == cid]
        if outgoing:
            neighbor_Rs = [concepts[e.target_id].retrievability for e in outgoing]
            avg_R = sum(neighbor_Rs) / len(neighbor_Rs)
            concept.interval_days = adjust_interval(concept.interval_days, avg_R)

        concept.stability_history.append(concept.stability)

        rating_names = {1: "Again", 2: "Hard", 3: "Good", 4: "Easy"}
        print(f"{step:4d} | {concept.title:25s} | {rating_names[rating]:6s} | {new_S_base:9.4f} | {concept.stability:10.4f} | {concept.stability - new_S_base:+8.4f}")

    # ── Results Summary ──────────────────────────────────────────────────────
    print("\n")
    print("=" * 80)
    print("  FINAL STATE COMPARISON: Standard FSRS vs Graph-Aware FSRS")
    print("=" * 80)
    print(f"{'Concept':25s} | {'S (Base)':>9s} | {'S (Graph)':>10s} | {'Diff':>8s} | {'Int(Base)':>9s} | {'Int(Graph)':>10s}")
    print("-" * 80)
    for cid in sorted(concepts.keys()):
        c = concepts[cid]
        b = baseline[cid]
        print(f"{c.title:25s} | {b.stability:9.4f} | {c.stability:10.4f} | {c.stability - b.stability:+8.4f} | {b.interval_days:9d} | {c.interval_days:10d}")

    # ── Propagation Events ────────────────────────────────────────────────────
    print("\n")
    print("=" * 80)
    print("  PROPAGATION EVENTS")
    print("=" * 80)
    if events:
        print(f"{'Step':>4} | {'Source':20s} → {'Target':20s} | {'Type':22s} | {'ΔS':>10s} | {'w_final':>8s}")
        print("-" * 95)
        for ev in events:
            src_name = concepts[ev.source_id].title
            tgt_name = concepts[ev.target_id].title
            print(f"{ev.step:4d} | {src_name:20s} → {tgt_name:20s} | {ev.event_type:22s} | {ev.delta_stability:+10.6f} | {ev.w_final_used:8.4f}")
    else:
        print("  No propagation events occurred.")

    # ── Edge Weight Evolution ─────────────────────────────────────────────────
    print("\n")
    print("=" * 80)
    print("  EDGE WEIGHT EVOLUTION (w_data learned from co-failures)")
    print("=" * 80)
    print(f"{'Edge':40s} | {'w_expert':>8s} | {'w_data':>7s} | {'w_final':>8s} | {'co_rev':>7s} | {'co_fail':>8s}")
    print("-" * 85)
    for edge in edges:
        src_name = concepts[edge.source_id].title
        tgt_name = concepts[edge.target_id].title
        label = f"{src_name} → {tgt_name}"
        print(f"{label:40s} | {edge.w_expert:8.4f} | {edge.w_data:7.4f} | {edge.w_final:8.4f} | {edge.co_review_count:7d} | {edge.co_fail_count:8d}")

    print("\n" + "=" * 80)
    print("  SIMULATION COMPLETE")
    print("=" * 80)
    print("""
Key observations:
  1. Standard FSRS treats each concept independently — identical math regardless.
  2. Graph-aware FSRS propagates failures: when Quadratic Eq fails, its parent
     (Algebra) and sibling (Quadratic Formula) also lose stability.
  3. Co-failure detection: Quadratic Eq and Quadratic Formula frequently fail
     together, so the w_data on their shared parent edges increases.
  4. Scheduling adjustment: concepts with weak neighbors are scheduled sooner.
""")


if __name__ == "__main__":
    run_simulation()
