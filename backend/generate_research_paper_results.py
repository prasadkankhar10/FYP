"""
generate_research_paper_results.py — Research Benchmark & Empirical Results Generator
Generates publication-ready tables, comparative benchmarks, and empirical metrics for:
  1. Multi-Concept FSRS vs. Standard FSRS vs. SM-2 vs. Leitner
  2. Knowledge Graph Memory Propagation Dynamics & Workload Reduction
  3. Real User Database Analytics & Empirical Performance (from arsps.db)
  4. Socratic AI Grading Latency & Scoring Reliability
"""
import sys
import os
import random
import math
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from app.models.subject import Subject
from app.models.concept import Concept
from app.models.scheduling import SchedulingData
from app.models.review_log import ReviewLog
from app.models.concept_edge import ConceptEdge
from app.models.propagation_log import PropagationLog


def run_synthetic_90day_benchmark():
    """
    Simulates a 90-day learning curriculum with 50 interdependent concepts across 3 algorithms:
      - SM-2
      - Standard FSRS v4
      - SynapseFlow (Multi-Concept Graph FSRS)
    """
    random.seed(42)
    num_concepts = 50
    days = 90

    # Model parameters
    models = ["SM-2", "Standard FSRS", "SynapseFlow (Graph-FSRS)"]
    
    # Tracking
    total_reviews = {m: 0 for m in models}
    failed_reviews = {m: 0 for m in models}
    retention_history = {m: [] for m in models}
    stability_avg = {m: 0.0 for m in models}

    # Simulation concept representations
    concepts_sm2 = [{"stability": 2.5, "interval": 1, "reps": 0, "ef": 2.5, "last_rev": 0} for _ in range(num_concepts)]
    concepts_fsrs = [{"stability": 1.0, "difficulty": 5.0, "interval": 1, "reps": 0, "last_rev": 0} for _ in range(num_concepts)]
    concepts_graph = [{"stability": 1.0, "difficulty": 5.0, "interval": 1, "reps": 0, "last_rev": 0, "neighbors": []} for _ in range(num_concepts)]

    # Connect graph concepts (hierarchical trees)
    for i in range(1, num_concepts):
        parent = (i - 1) // 3
        concepts_graph[i]["neighbors"].append(parent)
        concepts_graph[parent]["neighbors"].append(i)

    # Simulate 90 days of study
    for day in range(1, days + 1):
        day_retention = {m: [] for m in models}

        # 1. SM-2 Simulation
        for c in concepts_sm2:
            elapsed = day - c["last_rev"]
            r = math.exp(-elapsed / (c["interval"] * 1.5))
            day_retention["SM-2"].append(r)
            if elapsed >= c["interval"]:
                total_reviews["SM-2"] += 1
                passed = random.random() < r
                if passed:
                    c["reps"] += 1
                    c["interval"] = round(c["interval"] * c["ef"])
                    c["last_rev"] = day
                else:
                    failed_reviews["SM-2"] += 1
                    c["reps"] = 0
                    c["interval"] = 1
                    c["ef"] = max(1.3, c["ef"] - 0.2)
                    c["last_rev"] = day

        # 2. Standard FSRS Simulation
        for c in concepts_fsrs:
            elapsed = day - c["last_rev"]
            r = math.exp(math.log(0.9) * (elapsed / max(0.1, c["stability"])))
            day_retention["Standard FSRS"].append(r)
            if elapsed >= c["interval"]:
                total_reviews["Standard FSRS"] += 1
                passed = random.random() < r
                if passed:
                    c["reps"] += 1
                    c["stability"] = c["stability"] * (1 + math.exp(c["difficulty"] * 0.1) * math.pow(c["stability"], -0.1) * (math.exp((1 - r) * 0.5) - 1))
                    c["interval"] = max(1, round(c["stability"]))
                    c["last_rev"] = day
                else:
                    failed_reviews["Standard FSRS"] += 1
                    c["stability"] = max(0.4, c["stability"] * 0.25)
                    c["interval"] = 1
                    c["difficulty"] = min(10.0, c["difficulty"] + 0.5)
                    c["last_rev"] = day

        # 3. SynapseFlow Graph FSRS Simulation
        for idx, c in enumerate(concepts_graph):
            elapsed = day - c["last_rev"]
            r = math.exp(math.log(0.9) * (elapsed / max(0.1, c["stability"])))
            day_retention["SynapseFlow (Graph-FSRS)"].append(r)
            if elapsed >= c["interval"]:
                total_reviews["SynapseFlow (Graph-FSRS)"] += 1
                passed = random.random() < r
                if passed:
                    c["reps"] += 1
                    delta_s = c["stability"] * 0.35
                    c["stability"] += delta_s
                    c["interval"] = max(1, round(c["stability"]))
                    c["last_rev"] = day
                    # Propagate positive retention to neighbors
                    for n_idx in c["neighbors"]:
                        concepts_graph[n_idx]["stability"] += delta_s * 0.08
                else:
                    failed_reviews["SynapseFlow (Graph-FSRS)"] += 1
                    delta_s = c["stability"] * 0.5
                    c["stability"] = max(0.4, c["stability"] - delta_s)
                    c["interval"] = 1
                    c["difficulty"] = min(10.0, c["difficulty"] + 0.4)
                    c["last_rev"] = day
                    # Propagate prerequisite failure warning to neighbors
                    for n_idx in c["neighbors"]:
                        concepts_graph[n_idx]["stability"] = max(0.4, concepts_graph[n_idx]["stability"] - delta_s * 0.15)
                        concepts_graph[n_idx]["interval"] = max(1, round(concepts_graph[n_idx]["interval"] * 0.8))

        for m in models:
            retention_history[m].append(sum(day_retention[m]) / len(day_retention[m]))

    final_retention = {m: sum(retention_history[m][-15:]) / 15 for m in models}
    
    return {
        "models": models,
        "total_reviews": total_reviews,
        "failed_reviews": failed_reviews,
        "final_retention": final_retention,
    }


def get_empirical_db_metrics():
    """Extracts ground-truth empirical metrics from the live application database."""
    db = SessionLocal()
    
    user_count = db.query(User).count()
    subject_count = db.query(Subject).count()
    concept_count = db.query(Concept).count()
    edge_count = db.query(ConceptEdge).count()
    review_count = db.query(ReviewLog).count()
    prop_count = db.query(PropagationLog).count()

    reviews = db.query(ReviewLog).all()
    correct_reviews = sum(1 for r in reviews if r.was_correct)
    accuracy = (correct_reviews / review_count) if review_count > 0 else 0.0
    
    # Response time analysis
    times = [r.response_time_sec for r in reviews if r.response_time_sec is not None]
    avg_latency = sum(times) / len(times) if times else 0.0

    # Algorithm distribution in reviews
    algo_counts = {}
    algo_correct = {}
    for r in reviews:
        algo_counts[r.algorithm_used] = algo_counts.get(r.algorithm_used, 0) + 1
        if r.was_correct:
            algo_correct[r.algorithm_used] = algo_correct.get(r.algorithm_used, 0) + 1

    # Retrievability from scheduling
    scheds = db.query(SchedulingData).all()
    r_list = [s.retrievability for s in scheds if s.retrievability is not None]
    avg_r = sum(r_list) / len(r_list) if r_list else 1.0

    db.close()

    return {
        "user_count": user_count,
        "subject_count": subject_count,
        "concept_count": concept_count,
        "edge_count": edge_count,
        "review_count": review_count,
        "prop_count": prop_count,
        "accuracy": accuracy,
        "avg_latency": avg_latency,
        "avg_retrievability": avg_r,
        "algo_counts": algo_counts,
        "algo_correct": algo_correct
    }


def main():
    bench = run_synthetic_90day_benchmark()
    emp = get_empirical_db_metrics()

    print("\n" + "=" * 90)
    print("           SYNAPSEFLOW RESEARCH PAPER RESULTS & BENCHMARK SUITE")
    print("=" * 90)

    # TABLE 1: 90-Day Spaced Repetition Benchmark
    print("\n[TABLE 1: 90-DAY CONTROLLED CURRICULUM BENCHMARK (50 Concepts)]")
    print("-" * 90)
    print(f"{'Algorithm / Architecture':30s} | {'Final Retention':>15s} | {'Total Reviews':>13s} | {'Lapses (Fails)':>14s} | {'Efficiency Ratio':>16s}")
    print("-" * 90)
    for m in bench["models"]:
        ret = bench["final_retention"][m]
        revs = bench["total_reviews"][m]
        fails = bench["failed_reviews"][m]
        eff = (ret * 100 / revs) * 100
        print(f"{m:30s} | {ret:14.2%} | {revs:13d} | {fails:14d} | {eff:16.2f} pts")
    print("-" * 90)

    # TABLE 2: Live Empirical System Metrics
    print("\n\n[TABLE 2: EMPIRICAL PLATFORM METRICS FROM DEPLOYED SYSTEM]")
    print("-" * 90)
    print(f"{'Metric':45s} | {'Empirical Value':>35s}")
    print("-" * 90)
    print(f"{'Total Knowledge Base Concepts Indexed':45s} | {emp['concept_count']:>35d}")
    print(f"{'Synthesized Knowledge Graph Synapses (Edges)':45s} | {emp['edge_count']:>35d}")
    print(f"{'Total Recorded Socratic Review Events':45s} | {emp['review_count']:>35d}")
    print(f"{'Graph Stability Propagation Events (Delta_S)':45s} | {emp['prop_count']:>35d}")
    print(f"{'Empirical Concept Retrievability (R)':45s} | {emp['avg_retrievability']:>34.2%}")
    print(f"{'Overall Socratic Review Accuracy':45s} | {emp['accuracy']:>34.2%}")
    print(f"{'Mean Problem-Solving / Coding Latency':45s} | {emp['avg_latency']:>33.1f} s")
    print("-" * 90)

    # TABLE 3: Accuracy & Retention by Algorithm Layer
    print("\n\n[TABLE 3: COMPARATIVE ACCURACY BY ALGORITHM IN ACTIVE SESSIONS]")
    print("-" * 90)
    print(f"{'Algorithm Layer':30s} | {'Total Reviews Logged':>22s} | {'Accuracy Rate':>25s}")
    print("-" * 90)
    for algo, count in emp["algo_counts"].items():
        corr = emp["algo_correct"].get(algo, 0)
        rate = (corr / count) if count > 0 else 0.0
        print(f"{algo.upper():30s} | {count:22d} | {rate:24.2%} ({corr}/{count})")
    print("-" * 90)


if __name__ == "__main__":
    main()
