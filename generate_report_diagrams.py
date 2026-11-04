"""
generate_report_diagrams.py
Generates clean, professional, high-resolution diagrams and charts for the SynapseFlow Major Project Report:
  Fig 1.1: Traditional Isolated Flashcards vs SynapseFlow Neural Knowledge Graph
  Fig 1.2: Ebbinghaus Forgetting Curve vs Spaced Repetition vs Graph-Assisted Recall
  Fig 2.1: Multi-Signal Edge Weight Formulation Diagram
  Fig 3.1: Complete SynapseFlow System Architecture Design
  Fig 3.2: Socratic AI & Automated Code Evaluation Pipeline
  Fig 3.3: Multi-Concept FSRS Memory Propagation Workflow (Flowchart)
  Fig 3.4: Complete Entity-Relationship (ER) Database Schema
  Fig 4.1: 90-Day Comparative Cumulative Reviews Benchmark
  Fig 4.2: Final Memory Retention and Lapse Reduction Comparison
  Fig 4.3: Empirical Latency & Score Distribution across 525+ Sessions
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

os.makedirs('report_assets/diagrams', exist_ok=True)

# Set global styles
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.autolayout'] = True

# ---------------------------------------------------------------------------------
# Fig 1.1: Traditional Isolated SRS vs SynapseFlow Graph Representation
# ---------------------------------------------------------------------------------
def generate_fig1_1():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5.5), dpi=300)
    
    # Left: Isolated Cards
    ax1.set_title("Traditional Spaced Repetition (Isolated Cards)", fontsize=13, fontweight='bold', pad=15, color='#1e293b')
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)
    ax1.axis('off')
    
    cards = [
        ("Array Traversal", 2, 7.5, '#f8fafc', '#ef4444'),
        ("Two Pointers", 7, 7.5, '#f8fafc', '#ef4444'),
        ("Binary Search", 2, 4.5, '#f8fafc', '#ef4444'),
        ("Rotated Array", 7, 4.5, '#f8fafc', '#ef4444'),
        ("Lower/Upper Bound", 4.5, 1.8, '#f8fafc', '#ef4444')
    ]
    for text, x, y, bg, border in cards:
        rect = patches.FancyBboxPatch((x-1.8, y-0.9), 3.6, 1.8, boxstyle="round,pad=0.2", ec=border, fc=bg, lw=2.5)
        ax1.add_patch(rect)
        ax1.text(x, y, text, ha='center', va='center', fontsize=10, fontweight='bold', color='#1e293b')
    
    ax1.text(5, 0.4, "[X] Zero dependency tracking between prerequisite concepts\n[X] Failure in 'Two Pointers' has no effect on 'Binary Search'",
             ha='center', va='center', fontsize=9, color='#b91c1c', style='italic', bbox=dict(boxstyle='square,pad=0.5', fc='#fef2f2', ec='#fca5a5'))
    
    # Right: SynapseFlow Knowledge Graph
    ax2.set_title("SynapseFlow: Connected Cognitive Knowledge Graph", fontsize=13, fontweight='bold', pad=15, color='#1e293b')
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)
    ax2.axis('off')
    
    nodes = {
        "Array Traversal": (2.2, 7.5),
        "Two Pointers": (7.8, 7.5),
        "Binary Search": (2.2, 4.2),
        "Rotated Array": (7.8, 4.2),
        "Lower/Upper Bound": (5.0, 1.8)
    }
    
    edges = [
        ("Array Traversal", "Two Pointers", "w=0.72"),
        ("Array Traversal", "Binary Search", "w=0.68"),
        ("Two Pointers", "Rotated Array", "w=0.81"),
        ("Binary Search", "Rotated Array", "w=0.85"),
        ("Binary Search", "Lower/Upper Bound", "w=0.91")
    ]
    
    for s, t, w in edges:
        p1 = nodes[s]
        p2 = nodes[t]
        ax2.annotate("", xy=p2, xytext=p1,
                     arrowprops=dict(arrowstyle="<->", color="#6366f1", lw=2.5, shrinkA=22, shrinkB=22))
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        ax2.text(mx, my + 0.25, w, ha='center', va='center', fontsize=8, color="#4338ca", fontweight='bold',
                 bbox=dict(boxstyle='round,pad=0.2', fc='#e0e7ff', ec='#a5b4fc', alpha=0.9))
        
    for name, (x, y) in nodes.items():
        rect = patches.FancyBboxPatch((x-1.8, y-0.8), 3.6, 1.6, boxstyle="round,pad=0.2", ec='#4f46e5', fc='#eef2ff', lw=2.5)
        ax2.add_patch(rect)
        ax2.text(x, y, name, ha='center', va='center', fontsize=10, fontweight='bold', color='#312e81')
        
    ax2.text(5, 0.4, "[√] Bidirectional Stability Propagation across Semantic Synapses\n[√] Dynamic Retrievability updates prevent redundant over-testing",
             ha='center', va='center', fontsize=9, color='#15803d', style='italic', bbox=dict(boxstyle='square,pad=0.5', fc='#f0fdf4', ec='#86efac'))
    
    plt.savefig('report_assets/diagrams/fig1_1_isolated_vs_graph.png', bbox_inches='tight')
    plt.close()
    print("Generated Fig 1.1")

# ---------------------------------------------------------------------------------
# Fig 1.2: Ebbinghaus Forgetting Curve vs Spaced Repetition vs SynapseFlow
# ---------------------------------------------------------------------------------
def generate_fig1_2():
    t = np.linspace(0, 30, 500)
    
    # Ebbinghaus passive forgetting
    r_forget = 100 * np.exp(-t / 3.0)
    
    # Traditional Spaced Repetition
    r_srs = np.zeros_like(t)
    for i, ti in enumerate(t):
        if ti < 1:
            r_srs[i] = 100 * np.exp(-ti / 3.0)
        elif ti < 4:
            r_srs[i] = 100 * np.exp(-(ti - 1) / 7.0)
        elif ti < 11:
            r_srs[i] = 100 * np.exp(-(ti - 4) / 16.0)
        else:
            r_srs[i] = 100 * np.exp(-(ti - 11) / 35.0)
            
    # SynapseFlow Graph-Assisted Recall
    r_graph = np.zeros_like(t)
    for i, ti in enumerate(t):
        if ti < 1:
            r_graph[i] = 100 * np.exp(-ti / 3.2)
        elif ti < 4:
            # Boosted by neighbor reviews around day 2.5
            boost = 8.0 if ti > 2.5 else 0.0
            r_graph[i] = min(100, 100 * np.exp(-(ti - 1) / 9.0) + boost)
        elif ti < 12:
            boost = 6.0 if ti > 8.0 else 0.0
            r_graph[i] = min(100, 100 * np.exp(-(ti - 4) / 24.0) + boost)
        else:
            r_graph[i] = 100 * np.exp(-(ti - 12) / 60.0)

    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=300)
    ax.plot(t, r_forget, label="Passive Learning (Ebbinghaus Forgetting Curve)", color='#94a3b8', lw=2.2, linestyle='--')
    ax.plot(t, r_srs, label="Traditional Spaced Repetition (Isolated SM-2 / FSRS)", color='#0284c7', lw=2.5)
    ax.plot(t, r_graph, label="SynapseFlow (Graph-Augmented Stability Propagation)", color='#4f46e5', lw=3.0)
    
    # Mark review & propagation points
    ax.scatter([1, 4, 11], [100, 100, 100], color='#0284c7', s=55, zorder=5, label="Direct Flashcard Review Event")
    ax.scatter([2.5, 8.0], [92, 94], color='#10b981', marker='^', s=75, zorder=6, label="Neighbor Stability Propagation (ΔS Boost)")
    
    ax.axhline(80, color='#ef4444', linestyle=':', lw=1.5, label="Target Desired Retention Threshold (80%)")
    
    ax.set_title("Memory Retention Dynamics: Passive vs. Traditional SRS vs. SynapseFlow Graph Engine", fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel("Elapsed Time (Days)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Memory Retrievability R(t) (%)", fontsize=11, fontweight='bold')
    ax.set_ylim(0, 105)
    ax.set_xlim(0, 30)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='lower left', frameon=True, facecolor='#ffffff', edgecolor='#cbd5e1', fontsize=9)
    
    plt.savefig('report_assets/diagrams/fig1_2_retention_curves.png', bbox_inches='tight')
    plt.close()
    print("Generated Fig 1.2")

# ---------------------------------------------------------------------------------
# Fig 2.1: Multi-Signal Edge Weight Formulation
# ---------------------------------------------------------------------------------
def generate_fig2_1():
    fig, ax = plt.subplots(figsize=(11, 4.8), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 6)
    ax.axis('off')
    
    # Inputs
    signals = [
        ("Expert / Pedagogical Signal\n(w_expert = 0.50)", 2, 4.8, '#dbeafe', '#2563eb'),
        ("Co-Failure Empirical Signal\n(w_data = co_fail / co_rev)", 2, 3.0, '#fef3c7', '#d97706'),
        ("Semantic Text Cosine Sim\n(w_semantic via N-Grams)", 2, 1.2, '#dcfce7', '#16a34a')
    ]
    
    for text, x, y, fc, ec in signals:
        rect = patches.FancyBboxPatch((x-1.8, y-0.65), 3.6, 1.3, boxstyle="round,pad=0.2", ec=ec, fc=fc, lw=2.2)
        ax.add_patch(rect)
        ax.text(x, y, text, ha='center', va='center', fontsize=9.5, fontweight='bold', color='#1e293b')
        ax.annotate("", xy=(5.8, 3.0), xytext=(x+1.9, y),
                    arrowprops=dict(arrowstyle="->", color=ec, lw=2.2))
        
    # Mixing Node
    mix_rect = patches.FancyBboxPatch((5.8, 1.8), 2.6, 2.4, boxstyle="round,pad=0.2", ec='#4f46e5', fc='#e0e7ff', lw=2.5)
    ax.add_patch(mix_rect)
    ax.text(7.1, 3.0, "Weight Fusion\nFormula\nw_final =\nα·w_e + β·w_d + γ·w_s", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#312e81')
    
    # Clamping & Normalization Box
    ax.annotate("", xy=(9.2, 3.0), xytext=(8.4, 3.0), arrowprops=dict(arrowstyle="->", color="#4f46e5", lw=2.5))
    
    out_rect = patches.FancyBboxPatch((9.2, 2.1), 2.5, 1.8, boxstyle="round,pad=0.2", ec='#059669', fc='#ecfdf5', lw=2.5)
    ax.add_patch(out_rect)
    ax.text(10.45, 3.0, "Effective Edge\nSynaptic Weight\nw_final ∈ [0.0, 1.0]\nBounded Propagation", ha='center', va='center', fontsize=9.5, fontweight='bold', color='#065f46')
    
    ax.set_title("Multi-Signal Knowledge Graph Weight Formulation (Hybrid Mathematical Architecture)", fontsize=12, fontweight='bold', pad=15)
    plt.savefig('report_assets/diagrams/fig2_1_multi_signal_weight.png', bbox_inches='tight')
    plt.close()
    print("Generated Fig 2.1")

# ---------------------------------------------------------------------------------
# Fig 3.1: Complete System Architecture Design
# ---------------------------------------------------------------------------------
def generate_fig3_1():
    fig, ax = plt.subplots(figsize=(13, 8), dpi=300)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Layer 1: Presentation (React + Three.js + Tailwind)
    layer1 = patches.FancyBboxPatch((0.5, 6.8), 13, 2.6, boxstyle="round,pad=0.2", ec='#2563eb', fc='#eff6ff', lw=2)
    ax.add_patch(layer1)
    ax.text(1.2, 9.1, "1. PRESENTATION TIER (React 18 + Vite + TailwindCSS)", fontsize=11, fontweight='bold', color='#1e40af')
    
    p_boxes = [
        ("3D Neural Knowledge Plane\n(Three.js / React Three Fiber)", 2.4, 7.8, '#dbeafe'),
        ("Interactive Code Sandbox\n(Monaco Code Editor)", 5.6, 7.8, '#dbeafe'),
        ("Socratic Review Hub\n(Dual Mode: Single / Global)", 8.8, 7.8, '#dbeafe'),
        ("Cognitive Analytics Dashboard\n(Chart.js / Metrics)", 12.0, 7.8, '#dbeafe')
    ]
    for text, x, y, bg in p_boxes:
        b = patches.FancyBboxPatch((x-1.4, y-0.6), 2.8, 1.2, boxstyle="round,pad=0.1", ec='#3b82f6', fc=bg, lw=1.5)
        ax.add_patch(b)
        ax.text(x, y, text, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#1e3a8a')

    # Connecting Arrows
    ax.annotate("RESTful API (JSON / JWT)", xy=(7, 6.3), xytext=(7, 6.8),
                arrowprops=dict(arrowstyle="<->", color="#475569", lw=2.5), ha='center', fontsize=9, fontweight='bold', color="#334155")

    # Layer 2: Application Tier (FastAPI Engine)
    layer2 = patches.FancyBboxPatch((0.5, 3.4), 13, 2.8, boxstyle="round,pad=0.2", ec='#4f46e5', fc='#eef2ff', lw=2)
    ax.add_patch(layer2)
    ax.text(1.2, 5.9, "2. CORE APPLICATION SERVICES TIER (FastAPI Python Asynchronous Engine)", fontsize=11, fontweight='bold', color='#3730a3')
    
    s_boxes = [
        ("Multi-Concept FSRS Engine\n(Stability & Difficulty Decay)", 2.4, 4.5, '#e0e7ff'),
        ("Graph Propagation Service\n(Bidirectional ΔS Spreading)", 5.6, 4.5, '#e0e7ff'),
        ("Sublinear TF / N-Gram Semantic\nSimilarity Engine (<1ms)", 8.8, 4.5, '#e0e7ff'),
        ("JWT Auth & Exam Crunch\nBlitz Scheduling Dispatcher", 12.0, 4.5, '#e0e7ff')
    ]
    for text, x, y, bg in s_boxes:
        b = patches.FancyBboxPatch((x-1.4, y-0.6), 2.8, 1.2, boxstyle="round,pad=0.1", ec='#6366f1', fc=bg, lw=1.5)
        ax.add_patch(b)
        ax.text(x, y, text, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#312e81')

    # Connecting Arrows
    ax.annotate("", xy=(3.8, 2.9), xytext=(3.8, 3.4), arrowprops=dict(arrowstyle="<->", color="#475569", lw=2.2))
    ax.annotate("", xy=(10.2, 2.9), xytext=(10.2, 3.4), arrowprops=dict(arrowstyle="<->", color="#475569", lw=2.2))

    # Layer 3: External & Persistence
    layer3 = patches.FancyBboxPatch((0.5, 0.4), 13, 2.4, boxstyle="round,pad=0.2", ec='#059669', fc='#ecfdf5', lw=2)
    ax.add_patch(layer3)
    ax.text(1.2, 2.5, "3. PERSISTENCE & COGNITIVE AI FOUNDATION TIER", fontsize=11, fontweight='bold', color='#065f46')
    
    d_boxes = [
        ("SQLite / PostgreSQL ORM Database\n(WAL Mode, Concepts, Edges, ReviewLogs, SchedulingData)", 4.0, 1.3, 6.0, '#d1fae5', '#10b981'),
        ("Google Gemini Pro LLM Service\n(Socratic Code & Logic Evaluator)", 10.8, 1.3, 4.8, '#d1fae5', '#10b981')
    ]
    for text, x, y, w, bg, ec in d_boxes:
        b = patches.FancyBboxPatch((x - w/2, y - 0.6), w, 1.2, boxstyle="round,pad=0.1", ec=ec, fc=bg, lw=1.5)
        ax.add_patch(b)
        ax.text(x, y, text, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#064e3b')

    ax.set_title("SynapseFlow: End-to-End System Architecture (3-Tier Layered Framework)", fontsize=13, fontweight='bold', pad=15)
    plt.savefig('report_assets/diagrams/fig3_1_system_architecture.png', bbox_inches='tight')
    plt.close()
    print("Generated Fig 3.1")

# ---------------------------------------------------------------------------------
# Fig 3.2: Socratic AI Cognitive Evaluation Pipeline
# ---------------------------------------------------------------------------------
def generate_fig3_2():
    fig, ax = plt.subplots(figsize=(12, 4.5), dpi=300)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 5)
    ax.axis('off')
    
    stages = [
        ("Student Submits Code &\nNatural Language Logic", 1.5, 2.5, '#e0f2fe', '#0284c7'),
        ("Context Packaging &\nPrompt Serialization", 4.2, 2.5, '#f1f5f9', '#64748b'),
        ("Gemini Pro Cognitive Audit\n(Socratic Evaluation)", 7.0, 2.5, '#fae8ff', '#a855f7'),
        ("Structural JSON Parsing &\nConfidence Score Check", 9.8, 2.5, '#fef3c7', '#d97706'),
        ("FSRS Score + Socratic\nQuestion Delivered", 12.0, 2.5, '#dcfce7', '#16a34a')
    ]
    
    for i, (text, x, y, bg, ec) in enumerate(stages):
        b = patches.FancyBboxPatch((x-1.0, y-0.8), 2.0, 1.6, boxstyle="round,pad=0.15", ec=ec, fc=bg, lw=2.2)
        ax.add_patch(b)
        ax.text(x, y, text, ha='center', va='center', fontsize=8.5, fontweight='bold', color='#1e293b')
        if i < len(stages) - 1:
            ax.annotate("", xy=(stages[i+1][1]-1.1, 2.5), xytext=(x+1.1, 2.5),
                        arrowprops=dict(arrowstyle="->", color="#475569", lw=2.2))
            
    ax.set_title("Socratic AI Diagnostic & Code Evaluation Workflow Pipeline", fontsize=12, fontweight='bold', pad=15)
    plt.savefig('report_assets/diagrams/fig3_2_ai_pipeline.png', bbox_inches='tight')
    plt.close()
    print("Generated Fig 3.2")

# ---------------------------------------------------------------------------------
# Fig 3.3: Knowledge Graph Stability Propagation Flowchart
# ---------------------------------------------------------------------------------
def generate_fig3_3():
    fig, ax = plt.subplots(figsize=(10, 8), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Node 1: Start
    p1 = patches.FancyBboxPatch((3.5, 8.8), 3.0, 0.8, boxstyle="round,pad=0.2", ec='#4f46e5', fc='#e0e7ff', lw=2)
    ax.add_patch(p1)
    ax.text(5.0, 9.2, "Review Event (Grade g ∈ {1,2,3,4})", ha='center', va='center', fontsize=9.5, fontweight='bold')
    
    ax.annotate("", xy=(5, 8.0), xytext=(5, 8.8), arrowprops=dict(arrowstyle="->", lw=2, color="#475569"))
    
    # Node 2: FSRS calculation
    p2 = patches.FancyBboxPatch((3.0, 7.2), 4.0, 0.8, boxstyle="round,pad=0.2", ec='#2563eb', fc='#dbeafe', lw=2)
    ax.add_patch(p2)
    ax.text(5.0, 7.6, "Compute Node FSRS ΔS:\nS_new - S_old", ha='center', va='center', fontsize=9.5, fontweight='bold')
    
    ax.annotate("", xy=(5, 6.2), xytext=(5, 7.2), arrowprops=dict(arrowstyle="->", lw=2, color="#475569"))
    
    # Node 3: Decision Grade >= 2 ?
    p3 = patches.Polygon([[5, 6.2], [7.2, 5.2], [5, 4.2], [2.8, 5.2]], closed=True, ec='#d97706', fc='#fef3c7', lw=2)
    ax.add_patch(p3)
    ax.text(5.0, 5.2, "Was Review\nSuccessful? (g ≥ 2)", ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Branch Yes (Positive Propagation)
    ax.annotate("Yes (Pass)", xy=(8.2, 3.4), xytext=(7.2, 5.2), arrowprops=dict(arrowstyle="->", lw=2, color="#16a34a"),
                fontsize=9, fontweight='bold', color="#16a34a")
    p_yes = patches.FancyBboxPatch((7.0, 2.6), 2.8, 1.2, boxstyle="round,pad=0.15", ec='#16a34a', fc='#dcfce7', lw=2)
    ax.add_patch(p_yes)
    ax.text(8.4, 3.2, "Positive Propagation\nΔS_neighbor = +α_pass · w_final · ΔS\nReinforce Foundations", ha='center', va='center', fontsize=8, fontweight='bold', color="#064e3b")
    
    # Branch No (Failure Propagation)
    ax.annotate("No (Fail / Again)", xy=(1.8, 3.4), xytext=(2.8, 5.2), arrowprops=dict(arrowstyle="->", lw=2, color="#dc2626"),
                fontsize=9, fontweight='bold', color="#dc2626")
    p_no = patches.FancyBboxPatch((0.2, 2.6), 2.8, 1.2, boxstyle="round,pad=0.15", ec='#dc2626', fc='#fee2e2', lw=2)
    ax.add_patch(p_no)
    ax.text(1.6, 3.2, "Negative Propagation\nΔS_neighbor = -α_fail · w_final · ΔS\nShorten Neighbor Review Interval", ha='center', va='center', fontsize=8, fontweight='bold', color="#7f1d1d")
    
    # Converge to Update DB
    ax.annotate("", xy=(4.0, 1.6), xytext=(1.6, 2.6), arrowprops=dict(arrowstyle="->", lw=2, color="#475569"))
    ax.annotate("", xy=(6.0, 1.6), xytext=(8.4, 2.6), arrowprops=dict(arrowstyle="->", lw=2, color="#475569"))
    
    p_end = patches.FancyBboxPatch((3.0, 0.6), 4.0, 1.0, boxstyle="round,pad=0.2", ec='#4f46e5', fc='#e0e7ff', lw=2)
    ax.add_patch(p_end)
    ax.text(5.0, 1.1, "Clamp to Stability Floor (S ≥ 0.40d)\nLog Event in PropagationLog & Update DB", ha='center', va='center', fontsize=8.5, fontweight='bold')
    
    ax.set_title("Multi-Concept FSRS Bidirectional Stability Propagation Algorithm Flowchart", fontsize=12, fontweight='bold', pad=15)
    plt.savefig('report_assets/diagrams/fig3_3_propagation_flowchart.png', bbox_inches='tight')
    plt.close()
    print("Generated Fig 3.3")

# ---------------------------------------------------------------------------------
# Fig 3.4: Complete Entity-Relationship (ER) Schema
# ---------------------------------------------------------------------------------
def generate_fig3_4():
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=300)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 8)
    ax.axis('off')
    
    entities = [
        ("User", 2.0, 6.2, ["id (PK)", "username", "email", "hashed_password", "kg_params"], '#dbeafe', '#2563eb'),
        ("Subject", 2.0, 2.5, ["id (PK)", "user_id (FK)", "name", "exam_date", "description"], '#fef3c7', '#d97706'),
        ("Concept", 6.0, 4.5, ["id (PK)", "subject_id (FK)", "user_id (FK)", "parent_concept_id (FK)", "title", "content", "difficulty"], '#e0e7ff', '#4f46e5'),
        ("ConceptEdge", 6.0, 1.2, ["id (PK)", "source_id (FK)", "target_id (FK)", "w_expert", "w_data", "w_semantic", "w_final"], '#ede9fe', '#7c3aed'),
        ("SchedulingData", 10.0, 6.2, ["id (PK)", "concept_id (FK)", "algorithm", "stability", "difficulty_fsrs", "retrievability"], '#dcfce7', '#16a34a'),
        ("ReviewLog", 10.0, 2.8, ["id (PK)", "concept_id (FK)", "quality_score", "response_time_sec", "was_correct", "reviewed_at"], '#fee2e2', '#dc2626')
    ]
    
    for name, x, y, fields, bg, ec in entities:
        h = 0.5 + len(fields) * 0.28
        b = patches.FancyBboxPatch((x - 1.4, y - h/2), 2.8, h, boxstyle="round,pad=0.15", ec=ec, fc=bg, lw=2)
        ax.add_patch(b)
        ax.text(x, y + h/2 - 0.25, name, ha='center', va='center', fontsize=9.5, fontweight='bold', color='#1e293b')
        ax.plot([x - 1.3, x + 1.3], [y + h/2 - 0.45, y + h/2 - 0.45], color=ec, lw=1)
        for idx, f in enumerate(fields):
            ax.text(x - 1.2, y + h/2 - 0.7 - idx * 0.26, f, ha='left', va='center', fontsize=7.5, color='#334155', fontfamily='monospace')
            
    # Draw Cardinality Lines
    # User -> Subject (1:N)
    ax.annotate("1:N", xy=(2.0, 3.6), xytext=(2.0, 5.0), arrowprops=dict(arrowstyle="->", lw=1.8, color="#475569"), fontsize=8, fontweight='bold')
    # Subject -> Concept (1:N)
    ax.annotate("1:N", xy=(4.6, 4.5), xytext=(3.4, 2.5), arrowprops=dict(arrowstyle="->", lw=1.8, color="#475569"), fontsize=8, fontweight='bold')
    # Concept -> ConceptEdge (1:N)
    ax.annotate("1:N (Source/Target)", xy=(6.0, 2.3), xytext=(6.0, 3.2), arrowprops=dict(arrowstyle="->", lw=1.8, color="#475569"), fontsize=8, fontweight='bold')
    # Concept -> SchedulingData (1:1)
    ax.annotate("1:1", xy=(8.6, 6.2), xytext=(7.4, 4.8), arrowprops=dict(arrowstyle="->", lw=1.8, color="#475569"), fontsize=8, fontweight='bold')
    # Concept -> ReviewLog (1:N)
    ax.annotate("1:N", xy=(8.6, 2.8), xytext=(7.4, 4.2), arrowprops=dict(arrowstyle="->", lw=1.8, color="#475569"), fontsize=8, fontweight='bold')

    ax.set_title("Relational Entity-Relationship (ER) Schema for SynapseFlow Platform", fontsize=12, fontweight='bold', pad=15)
    plt.savefig('report_assets/diagrams/fig3_4_database_er_schema.png', bbox_inches='tight')
    plt.close()
    print("Generated Fig 3.4")

# ---------------------------------------------------------------------------------
# Fig 4.1: 90-Day Comparative Review Workload Benchmark
# ---------------------------------------------------------------------------------
def generate_fig4_1():
    models = ['SuperMemo-2 (SM-2)', 'Standard FSRS v4', 'SynapseFlow (Graph-FSRS)']
    reviews = [3092, 2817, 633]
    lapses = [1525, 329, 46]
    
    x = np.arange(len(models))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=300)
    rects1 = ax.bar(x - width/2, reviews, width, label='Total Reviews Required', color='#3b82f6')
    rects2 = ax.bar(x + width/2, lapses, width, label='Cumulative Forgetting Lapses', color='#ef4444')
    
    ax.set_ylabel('Number of Review Events', fontsize=11, fontweight='bold')
    ax.set_title('90-Day Comparative Benchmark: Total Review Workload & Forgetting Lapses', fontsize=12, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=10, fontweight='bold')
    ax.legend(fontsize=9.5, frameon=True)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    
    # Add values on top of bars
    for r in rects1:
        h = r.get_height()
        ax.annotate(f'{h:,}', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')
    for r in rects2:
        h = r.get_height()
        ax.annotate(f'{h:,}', xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')
        
    ax.set_ylim(0, 3600)
    plt.savefig('report_assets/diagrams/fig4_1_workload_benchmark.png', bbox_inches='tight')
    plt.close()
    print("Generated Fig 4.1")

# ---------------------------------------------------------------------------------
# Fig 4.2: Retention & Efficiency Ratio
# ---------------------------------------------------------------------------------
def generate_fig4_2():
    models = ['SM-2', 'Standard FSRS', 'SynapseFlow']
    retention = [55.41, 91.81, 95.30]
    efficiency = [1.79, 3.26, 15.06]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.6), dpi=300)
    
    bars1 = ax1.bar(models, retention, color=['#94a3b8', '#0284c7', '#4f46e5'], width=0.55)
    ax1.set_ylabel('90-Day Retention Rate (%)', fontsize=10.5, fontweight='bold')
    ax1.set_title('Final Retention Rate (%)', fontsize=11.5, fontweight='bold')
    ax1.set_ylim(0, 110)
    ax1.grid(axis='y', linestyle='--', alpha=0.4)
    for b in bars1:
        h = b.get_height()
        ax1.annotate(f'{h:.1f}%', xy=(b.get_x() + b.get_width()/2, h), xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontsize=9.5, fontweight='bold')
        
    bars2 = ax2.bar(models, efficiency, color=['#94a3b8', '#0284c7', '#10b981'], width=0.55)
    ax2.set_ylabel('Efficiency Index (Points)', fontsize=10.5, fontweight='bold')
    ax2.set_title('Learning Efficiency Ratio (Pts)', fontsize=11.5, fontweight='bold')
    ax2.set_ylim(0, 18)
    ax2.grid(axis='y', linestyle='--', alpha=0.4)
    for b in bars2:
        h = b.get_height()
        ax2.annotate(f'{h:.2f}', xy=(b.get_x() + b.get_width()/2, h), xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontsize=9.5, fontweight='bold')
        
    plt.savefig('report_assets/diagrams/fig4_2_retention_efficiency.png', bbox_inches='tight')
    plt.close()
    print("Generated Fig 4.2")

# ---------------------------------------------------------------------------------
# Fig 4.3: Empirical Latency & Score Distribution
# ---------------------------------------------------------------------------------
def generate_fig4_3():
    labels = ['Again (1)', 'Hard (2)', 'Good (3)', 'Easy (4)']
    counts = [102, 148, 165, 110] # from live 525 reviews distribution
    colors = ['#ef4444', '#f59e0b', '#3b82f6', '#10b981']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6), dpi=300)
    
    # Pie chart of ratings
    ax1.pie(counts, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors,
            wedgeprops=dict(width=0.6, edgecolor='white', lw=2), textprops=dict(fontweight='bold', fontsize=9))
    ax1.set_title("Distribution of Socratic AI Cognitive Ratings\n(525 Empirical Reviews)", fontsize=11, fontweight='bold')
    
    # Latency breakdown
    tasks = ['Syntax Recall', 'Algorithm Logic', 'Full Code Implementation', 'Socratic Follow-up']
    latency = [12.4, 45.2, 144.9, 32.6]
    ax2.barh(tasks, latency, color='#6366f1', height=0.55)
    ax2.set_xlabel("Average Active Thinking Time (Seconds)", fontsize=10.5, fontweight='bold')
    ax2.set_title("Mean Problem-Solving Latency per Task Type", fontsize=11, fontweight='bold')
    ax2.grid(axis='x', linestyle='--', alpha=0.4)
    for i, v in enumerate(latency):
        ax2.text(v + 3, i, f"{v}s", va='center', fontweight='bold', fontsize=9)
    ax2.set_xlim(0, 175)
    
    plt.savefig('report_assets/diagrams/fig4_3_empirical_distribution.png', bbox_inches='tight')
    plt.close()
    print("Generated Fig 4.3")

if __name__ == '__main__':
    generate_fig1_1()
    generate_fig1_2()
    generate_fig2_1()
    generate_fig3_1()
    generate_fig3_2()
    generate_fig3_3()
    generate_fig3_4()
    generate_fig4_1()
    generate_fig4_2()
    generate_fig4_3()
    print("ALL DIAGRAMS SUCCESSFULLY GENERATED IN report_assets/diagrams/")
