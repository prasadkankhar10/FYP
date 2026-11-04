# -*- coding: utf-8 -*-
"""
Generates the self-contained HTML/CSS/JS presentation for SynapseFlow.
Runs locally in any browser with zero dependencies, full offline support,
built-in speaker notes, keyboard shortcuts, and responsive 16:9 layout.
"""

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SynapseFlow: Academic Project Review Presentation</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-base: #0a0f1d;
    --bg-surface: #111827;
    --bg-card: rgba(17, 24, 39, 0.75);
    --border-subtle: rgba(255, 255, 255, 0.08);
    --border-highlight: rgba(59, 130, 246, 0.35);
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --accent-blue: #3b82f6;
    --accent-indigo: #6366f1;
    --accent-cyan: #06b6d4;
    --accent-emerald: #10b981;
    --accent-amber: #f59e0b;
    --accent-rose: #f43f5e;
    --grad-primary: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    --grad-glow: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(139, 92, 246, 0.05) 100%);
    --shadow-card: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    --radius-lg: 16px;
    --radius-md: 10px;
    --radius-sm: 6px;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background-color: var(--bg-base);
    color: var(--text-primary);
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
    height: 100vh;
    overflow: hidden;
    user-select: none;
    display: flex;
    flex-direction: column;
  }

  /* Presentation Container 16:9 Aspect Ratio */
  .viewport-wrapper {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    padding: 16px;
  }

  .slide-container {
    width: 100%;
    max-width: 1320px;
    aspect-ratio: 16 / 9;
    max-height: calc(100vh - 100px);
    background: radial-gradient(circle at 15% 15%, rgba(30, 58, 138, 0.15) 0%, transparent 50%),
                radial-gradient(circle at 85% 85%, rgba(88, 28, 135, 0.12) 0%, transparent 50%),
                var(--bg-surface);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-lg);
    box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.7);
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  /* Slide Management */
  .slide {
    position: absolute;
    inset: 0;
    padding: 44px 56px;
    display: flex;
    flex-direction: column;
    opacity: 0;
    pointer-events: none;
    transform: translateY(12px) scale(0.99);
    transition: opacity 0.35s cubic-bezier(0.16, 1, 0.3, 1), transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  }

  .slide.active {
    opacity: 1;
    pointer-events: auto;
    transform: translateY(0) scale(1);
    z-index: 2;
  }

  /* Header Typography */
  .slide-header {
    margin-bottom: 24px;
    flex-shrink: 0;
  }
  .kicker {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.8rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--accent-cyan);
    margin-bottom: 6px;
  }
  .kicker::before {
    content: '';
    display: inline-block;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: var(--accent-cyan);
  }
  .slide-title {
    font-size: 2.1rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    line-height: 1.15;
    background: linear-gradient(180deg, #ffffff 0%, #cbd5e1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .slide-subtitle {
    font-size: 1.0rem;
    color: var(--text-secondary);
    margin-top: 4px;
  }

  /* Layout Grids */
  .slide-body {
    flex: 1;
    display: flex;
    gap: 32px;
    min-height: 0;
    align-items: center;
  }
  .grid-2col {
    display: grid;
    grid-template-columns: 1.1fr 1fr;
    gap: 28px;
    width: 100%;
    height: 100%;
    align-items: center;
  }
  .grid-3col {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    width: 100%;
    height: 100%;
    align-items: center;
  }

  /* Reusable Visual Cards */
  .card {
    background: var(--bg-card);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 22px;
    transition: border-color 0.2s, transform 0.2s;
  }
  .card:hover {
    border-color: var(--border-highlight);
  }
  .card-highlight {
    background: var(--grad-glow);
    border: 1px solid rgba(59, 130, 246, 0.4);
  }
  .card h3 {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .card p {
    font-size: 0.92rem;
    line-height: 1.5;
    color: var(--text-secondary);
  }

  /* Stat & KPI Callouts */
  .stat-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    width: 100%;
  }
  .stat-card {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    padding: 16px 18px;
    text-align: center;
  }
  .stat-value {
    font-size: 2.2rem;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    line-height: 1.1;
  }
  .stat-label {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
    margin-top: 6px;
    font-weight: 600;
  }
  .color-emerald { color: var(--accent-emerald); }
  .color-blue { color: var(--accent-blue); }
  .color-cyan { color: var(--accent-cyan); }
  .color-amber { color: var(--accent-amber); }
  .color-rose { color: var(--accent-rose); }

  /* Formula Block */
  .formula-box {
    background: rgba(10, 15, 29, 0.85);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: var(--radius-md);
    padding: 16px 20px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.95rem;
    color: #e0e7ff;
    margin: 12px 0;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.4);
  }

  /* Image & Diagram Frame */
  .diagram-frame {
    width: 100%;
    height: 100%;
    max-height: 380px;
    background: #090d16;
    border: 1px solid var(--border-subtle);
    border-radius: var(--radius-md);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    position: relative;
    padding: 8px;
  }
  .diagram-frame img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    border-radius: calc(var(--radius-md) - 4px);
    transition: transform 0.3s;
  }
  .diagram-frame:hover img {
    transform: scale(1.02);
  }
  .diagram-caption {
    position: absolute;
    bottom: 8px;
    left: 12px;
    background: rgba(10, 15, 29, 0.85);
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.72rem;
    color: var(--text-muted);
    font-family: 'JetBrains Mono', monospace;
    border: 1px solid var(--border-subtle);
  }

  /* Table Style */
  .academic-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
    text-align: left;
  }
  .academic-table th {
    background: rgba(30, 41, 59, 0.8);
    color: var(--text-primary);
    padding: 10px 12px;
    font-weight: 600;
    border-bottom: 2px solid rgba(255, 255, 255, 0.1);
  }
  .academic-table td {
    padding: 10px 12px;
    border-bottom: 1px solid var(--border-subtle);
    color: var(--text-secondary);
  }
  .academic-table tr.highlight-row {
    background: rgba(59, 130, 246, 0.12);
    font-weight: 600;
  }
  .academic-table tr.highlight-row td {
    color: #93c5fd;
  }

  /* Tags & Badges */
  .badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    background: rgba(255, 255, 255, 0.08);
    color: var(--text-secondary);
  }
  .badge-blue { background: rgba(59, 130, 246, 0.2); color: #93c5fd; border: 1px solid rgba(59, 130, 246, 0.4); }
  .badge-emerald { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; border: 1px solid rgba(16, 185, 129, 0.4); }

  /* Bottom Presentation Control Bar */
  .deck-controls {
    height: 60px;
    background: #090d16;
    border-top: 1px solid var(--border-subtle);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 24px;
    z-index: 10;
  }
  .controls-left, .controls-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .btn-ctrl {
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid var(--border-subtle);
    color: var(--text-secondary);
    padding: 7px 14px;
    border-radius: var(--radius-sm);
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: all 0.2s;
  }
  .btn-ctrl:hover {
    background: rgba(255, 255, 255, 0.12);
    color: var(--text-primary);
  }
  .btn-ctrl.active-ctrl {
    background: var(--accent-blue);
    color: #fff;
    border-color: var(--accent-blue);
  }

  .slide-counter {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.88rem;
    color: var(--text-muted);
  }
  .slide-counter span {
    color: var(--text-primary);
    font-weight: 700;
  }

  .progress-bar-container {
    flex: 1;
    max-width: 320px;
    height: 4px;
    background: rgba(255, 255, 255, 0.08);
    border-radius: 2px;
    overflow: hidden;
  }
  .progress-bar-fill {
    height: 100%;
    width: 10%;
    background: var(--grad-primary);
    transition: width 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  }

  /* Speaker Notes Drawer */
  .speaker-drawer {
    position: fixed;
    bottom: 60px;
    left: 0;
    right: 0;
    background: rgba(10, 15, 29, 0.96);
    backdrop-filter: blur(20px);
    border-top: 1px solid var(--accent-indigo);
    padding: 20px 32px;
    max-height: 220px;
    overflow-y: auto;
    transform: translateY(100%);
    transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    z-index: 9;
    box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.7);
  }
  .speaker-drawer.open {
    transform: translateY(0);
  }
  .speaker-drawer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 6px;
  }
  .speaker-drawer-title {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 700;
    color: var(--accent-cyan);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .speaker-notes-content {
    font-size: 0.95rem;
    line-height: 1.6;
    color: #e2e8f0;
  }
  .speaker-notes-content b {
    color: #93c5fd;
  }
</style>
</head>
<body>

<div class="viewport-wrapper">
  <div class="slide-container" id="slideDeck">

    <!-- SLIDE 1: COVER -->
    <section class="slide active" data-title="Title & Cover" data-speaker="Prasad"
      data-notes="Respected members of the examination committee and research guide Dr. Arti Mohanpurkar. Welcome to our Major Project presentation on SYNAPSEFLOW. Developed at the Department of Computer Science and Engineering, Maharashtra Institute of Technology, Chhatrapati Sambhajinagar. Our team comprises Prasad Anil Kankhar, Prashant Anil Gande, and Aditya Devidas Kavde. Today we present an adaptive knowledge graph memory engine for technical education.">
      <div style="height:100%; display:flex; flex-direction:column; justify-content:space-between;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <img src="../report_assets/mit_csn_logo.png" alt="MIT CSN Logo" style="height:48px; object-fit:contain; filter:drop-shadow(0 2px 8px rgba(0,0,0,0.4));">
          <span class="badge badge-blue">Major Project-II · Academic Year 2026–2027</span>
        </div>
        
        <div style="margin: 20px 0;">
          <div class="kicker">B.Tech Project Presentation</div>
          <h1 style="font-size:2.4rem; font-weight:800; line-height:1.15; margin-bottom:12px; background:linear-gradient(135deg, #ffffff 40%, #93c5fd 100%); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
            SYNAPSEFLOW
          </h1>
          <h2 style="font-size:1.25rem; font-weight:500; color:#94a3b8; max-width:850px; line-height:1.4;">
            An Adaptive Multi-Concept Knowledge Graph and Socratic AI-Powered Spaced Repetition System
          </h2>
        </div>

        <div style="display:grid; grid-template-columns: 2fr 1.2fr; gap:24px; background:rgba(15,23,42,0.6); padding:20px 24px; border-radius:var(--radius-md); border:1px solid var(--border-subtle);">
          <div>
            <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted); margin-bottom:6px; font-weight:700;">Project Candidates</div>
            <div style="display:flex; gap:16px; flex-wrap:wrap; font-size:0.9rem; font-weight:600;">
              <span>Prasad Anil Kankhar <span style="color:var(--accent-cyan); font-family:'JetBrains Mono'; font-size:0.8rem;">(BT42036)</span></span>
              <span>•</span>
              <span>Prashant Anil Gande <span style="color:var(--accent-cyan); font-family:'JetBrains Mono'; font-size:0.8rem;">(BT42002)</span></span>
              <span>•</span>
              <span>Aditya Devidas Kavde <span style="color:var(--accent-cyan); font-family:'JetBrains Mono'; font-size:0.8rem;">(BT42043)</span></span>
            </div>
          </div>
          <div>
            <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted); margin-bottom:6px; font-weight:700;">Research Mentorship</div>
            <div style="font-size:0.9rem; font-weight:600;">
              Guide: <span style="color:#f8fafc;">Dr. Arti Mohanpurkar</span>
            </div>
            <div style="font-size:0.78rem; color:var(--text-muted); margin-top:2px;">
              HOD: Dr. Smita Kasar | Director: Dr. N. G. Patil
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 2: MOTIVATION & PROBLEM -->
    <section class="slide" data-title="The Core Problem" data-speaker="Prasad"
      data-notes="Traditional spaced repetition systems like Anki and SM-2 assume each card is an independent atom. In Computer Science, concepts are hierarchical. For example, mastering Dynamic Programming requires Recursion and Memoization. If a student forgets recursion, Anki does not propagate this failure to dependent topics, leading to catastrophic forgetting lapses. Furthermore, self-grading buttons like Again, Hard, Good, Easy introduce massive human subjective bias.">
      <div class="slide-header">
        <div class="kicker">Motivation & Challenges</div>
        <div class="slide-title">The Fundamental Flaws of Traditional SRS</div>
        <div class="slide-subtitle">Why isolated flashcard algorithms fail in technical, hierarchical disciplines</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:16px;">
            <div class="card" style="border-left:4px solid var(--accent-rose);">
              <h3><span class="color-rose">⚠️ Flaw 1:</span> Atomic Concept Isolation</h3>
              <p>Legacy SRS (SM-2, Anki) treats cards as independent atoms. In software engineering, topics are deeply intertwined. Forgetting a prerequisite leads to cascade errors that isolated schedules cannot detect.</p>
            </div>
            <div class="card" style="border-left:4px solid var(--accent-amber);">
              <h3><span class="color-amber">⚠️ Flaw 2:</span> Subjective Self-Grading Bias</h3>
              <p>Manual grading buttons (<i>Again, Hard, Good, Easy</i>) induce cognitive fatigue and Dunning-Kruger overconfidence. They provide zero technical feedback on <b>why</b> code failed.</p>
            </div>
            <div class="card card-highlight">
              <h3><span class="color-cyan">💡 The Solution:</span> SynapseFlow</h3>
              <p>Combines <b>Free Spaced Repetition (FSRS v4)</b> with a <b>Knowledge Graph Memory Engine</b> and <b>Socratic AI code evaluation</b>.</p>
            </div>
          </div>
          <div class="diagram-frame">
            <img src="../report_assets/diagrams/fig1_1_isolated_vs_graph.png" alt="Isolated SRS vs Graph SRS Topology">
            <span class="diagram-caption">Fig 1.1: Atomic Flashcards vs Graph Topology</span>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 3: SYSTEM ARCHITECTURE -->
    <section class="slide" data-title="System Architecture" data-speaker="Prashant"
      data-notes="SynapseFlow is architected across three core modules: First, a directed Knowledge Graph where concepts are nodes and dependencies are synapses. Second, the Multi-Concept FSRS Engine with asymmetric stability propagation. Third, a real-time Socratic AI Evaluator powered by Monaco Editor. When a review is performed, memory stability propagates outward across adjacent nodes.">
      <div class="slide-header">
        <div class="kicker">System Design</div>
        <div class="slide-title">Three Pillars of SynapseFlow Architecture</div>
        <div class="slide-subtitle">High-Level Design integrating cognitive modeling with topological graph dynamics</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:14px;">
            <div class="card">
              <h3><span class="badge badge-blue">Pillar 1</span> Directed Knowledge Graph</h3>
              <p>Curriculum concepts are modeled as vertices $V$. Inter-concept dependencies and prerequisites form weighted directed edges $E$ with sub-millisecond graph traversal.</p>
            </div>
            <div class="card">
              <h3><span class="badge badge-blue">Pillar 2</span> Asymmetric Stability Propagation</h3>
              <p>Dynamic FSRS v4 memory scheduling propagates stability deltas across 1-hop neighbours. Pass events reinforce prerequisites; fail events penalize prerequisites to prevent forgetting.</p>
            </div>
            <div class="card">
              <h3><span class="badge badge-blue">Pillar 3</span> Socratic AI Code Evaluator</h3>
              <p>Monaco editor captures live implementation code. LLM verifies algorithmic correctness, assigning objective continuous retention scores and conceptual hints.</p>
            </div>
          </div>
          <div class="diagram-frame">
            <img src="../report_assets/diagrams/fig3_1_system_architecture.png" alt="SynapseFlow System Architecture HLD">
            <span class="diagram-caption">Fig 3.1: High-Level System Architecture</span>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 4: MATHEMATICAL MODEL -->
    <section class="slide" data-title="Mathematical Formulation" data-speaker="Prashant"
      data-notes="Our mathematical model introduces two novel formulations. First, the Synaptic Edge Weight fuses semantic embedding distance, pedagogical prerequisite depth, and real-time co-failure probability. Second, the stability propagation equation updates adjacent nodes with asymmetric factors: alpha_pass equals 0.05, while alpha_fail equals 0.15. This asymmetry aggressively shields against prerequisite decay upon an advanced topic failure.">
      <div class="slide-header">
        <div class="kicker">Mathematical Model</div>
        <div class="slide-title">Multi-Signal Weights & Dynamic Propagation</div>
        <div class="slide-subtitle">Formulating human memory dynamics across hierarchical conceptual graphs</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:12px;">
            <div class="card">
              <h3 style="font-size:1.0rem;">1. Synaptic Edge Weight Fusion</h3>
              <div class="formula-box">
                w_{uv} = 0.35·S_{sem} + 0.45·W_{ped} + 0.20·P_{fail}
              </div>
              <p style="font-size:0.85rem;">Fuses embedding similarity ($\lambda_{sem}=0.35$), curriculum prerequisite depth ($\lambda_{ped}=0.45$), and observed co-failure probability ($\lambda_{data}=0.20$).</p>
            </div>
            <div class="card">
              <h3 style="font-size:1.0rem;">2. Asymmetric Stability Propagation</h3>
              <div class="formula-box">
                ΔS_v = α · w_{uv} · ΔS_u
              </div>
              <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:8px;">
                <div style="background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); padding:8px 12px; border-radius:6px;">
                  <b class="color-emerald">α_pass = 0.05</b>
                  <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:2px;">Conservative forward boost</div>
                </div>
                <div style="background:rgba(244,63,94,0.1); border:1px solid rgba(244,63,94,0.3); padding:8px 12px; border-radius:6px;">
                  <b class="color-rose">α_fail = 0.15</b>
                  <div style="font-size:0.75rem; color:var(--text-secondary); margin-top:2px;">Aggressive backward penalty</div>
                </div>
              </div>
            </div>
          </div>
          <div class="diagram-frame">
            <img src="../report_assets/diagrams/fig2_1_multi_signal_weight.png" alt="Multi-Signal Weighting Scheme">
            <span class="diagram-caption">Fig 2.1: Multi-Signal Weighting Scheme</span>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 5: IMPLEMENTATION & WORKFLOW -->
    <section class="slide" data-title="Implementation Pipeline" data-speaker="Prashant"
      data-notes="On the implementation front, our frontend is built with React 18, Vite, and WebGL Canvas using react-force-graph-2d for 60 FPS graph rendering. The backend runs FastAPI and Supabase PostgreSQL. When a student codes in the embedded Monaco editor, the submission is parsed against test cases and an LLM evaluation rubric, producing instant Socratic feedback and triggering graph-wide updates.">
      <div class="slide-header">
        <div class="kicker">Implementation & Stack</div>
        <div class="slide-title">Full-Stack Execution Pipeline</div>
        <div class="slide-subtitle">Low-Latency graph traversal and real-time Socratic feedback loop</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:14px;">
            <div class="card">
              <h3>Frontend & Visualization</h3>
              <p><b>React 18 + Vite + Tailwind CSS</b>. Renders force-directed graphs client-side using WebGL/Canvas (<span style="font-family:'JetBrains Mono'; font-size:0.8rem; color:var(--accent-cyan);">react-force-graph-2d</span>) at 60 FPS.</p>
            </div>
            <div class="card">
              <h3>Backend & Memory Engine</h3>
              <p><b>FastAPI + Supabase PostgreSQL</b>. Graph propagation executed via Python NetworkX with sub-linear response latency (&lt;25ms).</p>
            </div>
            <div class="card">
              <h3>Evaluation & Editor Interface</h3>
              <p>Embedded <b>Monaco Editor</b> provides native syntax highlighting, autocompletion, and real-time Socratic hints for technical challenges.</p>
            </div>
          </div>
          <div class="diagram-frame">
            <img src="../report_assets/diagrams/fig3_3_propagation_flowchart.png" alt="Memory Propagation Flowchart">
            <span class="diagram-caption">Fig 3.3: Low-Level Propagation Flowchart</span>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 6: PRODUCT SHOWCASE & DEMO -->
    <section class="slide" data-title="Product Showcase" data-speaker="Aditya"
      data-notes="Here is the live SynapseFlow application interface. Students view their entire curriculum as an interactive 3D/2D neural graph. Green nodes represent high retention stability; amber and red represent concepts decaying toward the forgetting threshold. Selecting a node opens the Monaco code studio with dynamic Socratic challenges. Submitting code recalculates memory stability across all prerequisite concepts in real-time.">
      <div class="slide-header">
        <div class="kicker">Live Demonstration</div>
        <div class="slide-title">Interactive Learning Workspace</div>
        <div class="slide-subtitle">Unified environment connecting concept graphs, code studio, and real-time analytics</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:14px;">
            <div class="card">
              <h3>1. Interactive Knowledge Canvas</h3>
              <p>Dynamic color-coding based on live stability $S$: <span class="badge badge-emerald">Green ≥ 10d</span> <span class="badge" style="background:rgba(245,158,11,0.2); color:#fcd34d;">Amber 3-10d</span> <span class="badge" style="background:rgba(244,63,94,0.2); color:#fda4af;">Red &lt; 3d</span>.</p>
            </div>
            <div class="card">
              <h3>2. Socratic AI Coding Studio</h3>
              <p>Students solve algorithmic tasks directly inside the Monaco editor. The AI provides tailored pedagogical hints without revealing the full solution.</p>
            </div>
            <div class="card">
              <h3>3. Dynamic Mastery Radar</h3>
              <p>Real-time analytics monitor retention probability, scheduled review queues, and projected memory decay across full technical curricula.</p>
            </div>
          </div>
          <div class="diagram-frame" style="background:#0b1120; border:1px solid rgba(59,130,246,0.3);">
            <img src="../report_assets/diagrams/fig3_5_ui_workspace_architecture.png" alt="SynapseFlow Web UI Workspace">
            <span class="diagram-caption">Fig 3.5: Workspace Architecture & UI Layout</span>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 7: BENCHMARK RESULTS 1 -->
    <section class="slide" data-title="Simulation Benchmark" data-speaker="Aditya"
      data-notes="We validated SynapseFlow through two rigorous evaluations. First, in a 90-day semester simulation across 100 concepts, SynapseFlow reduced total review workload by 77.5%, requiring only 633 reviews compared to 2,817 in SM-2. Most remarkably, forgetting lapses were slashed by 97.0% down to just 46 lapses, while sustaining a 95.3% retention rate.">
      <div class="slide-header">
        <div class="kicker">Experimental Validation</div>
        <div class="slide-title">90-Day Controlled Simulation Benchmark</div>
        <div class="slide-subtitle">Simulating semester-long learning across 100 interconnected Computer Science concepts</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:16px;">
            <div class="stat-grid">
              <div class="stat-card">
                <div class="stat-value color-emerald">-77.5%</div>
                <div class="stat-label">Review Workload</div>
              </div>
              <div class="stat-card">
                <div class="stat-value color-blue">46</div>
                <div class="stat-label">Lapses (vs 1525)</div>
              </div>
              <div class="stat-card">
                <div class="stat-value color-cyan">95.3%</div>
                <div class="stat-label">Target Retention</div>
              </div>
            </div>

            <table class="academic-table" style="background:rgba(15,23,42,0.6); border-radius:8px; overflow:hidden;">
              <thead>
                <tr>
                  <th>Algorithm</th>
                  <th>Reviews</th>
                  <th>Lapses</th>
                  <th>Retention</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>SM-2 (Anki Baseline)</td>
                  <td>2,817</td>
                  <td>1,525</td>
                  <td>90.2%</td>
                </tr>
                <tr>
                  <td>FSRS v4 (Isolated)</td>
                  <td>1,091</td>
                  <td>329</td>
                  <td>94.1%</td>
                </tr>
                <tr class="highlight-row">
                  <td><b>SynapseFlow (Ours)</b></td>
                  <td><b>633</b></td>
                  <td><b>46</b></td>
                  <td><b>95.3%</b></td>
                </tr>
              </tbody>
            </table>

            <div class="card" style="padding:12px 16px;">
              <p style="font-size:0.85rem;"><b>Key Takeaway:</b> Graph propagation prevents cascading prerequisite failures, eliminating over 1,400 wasted repetitive review sessions.</p>
            </div>
          </div>

          <div class="diagram-frame">
            <img src="../report_assets/diagrams/fig4_1_workload_benchmark.png" alt="Workload Benchmark Comparison">
            <span class="diagram-caption">Fig 4.1: Review Workload & Lapse Reduction</span>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 8: BENCHMARK RESULTS 2 -->
    <section class="slide" data-title="Empirical Benchmark" data-speaker="Aditya"
      data-notes="Second, we tested SynapseFlow on the official open Spaced Repetition Benchmark using empirical real-student telemetry comprising 600 reviews across 165 concepts and 582 graph edges. SynapseFlow achieved the lowest Log Loss at 0.5062, highest AUC at 0.5783, and reduced 20-bin RMSE to 0.1059, outperforming standard FSRS by 19.4% and SM-2 by 74.6%.">
      <div class="slide-header">
        <div class="kicker">Official SRS Benchmark</div>
        <div class="slide-title">Empirical Real Student Telemetry Analysis</div>
        <div class="slide-subtitle">Evaluated on real student logs across 165 concepts and 582 topological graph edges</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:16px;">
            <div class="stat-grid">
              <div class="stat-card">
                <div class="stat-value color-emerald">0.5062</div>
                <div class="stat-label">Log Loss (Best)</div>
              </div>
              <div class="stat-card">
                <div class="stat-value color-blue">0.1059</div>
                <div class="stat-label">20-Bin RMSE</div>
              </div>
              <div class="stat-card">
                <div class="stat-value color-cyan">+19.4%</div>
                <div class="stat-label">FSRS Accuracy Gain</div>
              </div>
            </div>

            <table class="academic-table" style="background:rgba(15,23,42,0.6); border-radius:8px; overflow:hidden;">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Log Loss ↓</th>
                  <th>RMSE (20-bin) ↓</th>
                  <th>AUC ↑</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>SuperMemo (SM-2)</td>
                  <td>0.6288</td>
                  <td>0.4172</td>
                  <td>0.5042</td>
                </tr>
                <tr>
                  <td>FSRS v4.5 (Standalone)</td>
                  <td>0.5642</td>
                  <td>0.1314</td>
                  <td>0.5312</td>
                </tr>
                <tr class="highlight-row">
                  <td><b>SynapseFlow (Ours)</b></td>
                  <td><b>0.5062</b></td>
                  <td><b>0.1059</b></td>
                  <td><b>0.5783</b></td>
                </tr>
              </tbody>
            </table>

            <div class="card" style="padding:12px 16px;">
              <p style="font-size:0.85rem;"><b>Empirical Proof:</b> Real students learn in non-linear conceptual networks; graph-aware scheduling dramatically improves real-world retention predictions.</p>
            </div>
          </div>

          <div class="diagram-frame">
            <img src="../report_assets/diagrams/fig4_2_retention_efficiency.png" alt="Retention Efficiency Curve">
            <span class="diagram-caption">Fig 4.2: Retention Efficiency & Calibration</span>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 9: SDGS & ENVIRONMENT -->
    <section class="slide" data-title="SDGs & Environment" data-speaker="Prasad"
      data-notes="SynapseFlow is built with sustainable impact at its core. It directly supports UN Sustainable Development Goal 4 for Quality Education by democratizing high-quality, personalized technical tutoring. In terms of green computing, client-side WebGL graph rendering and aggressive API caching restricted total development electricity consumption to just 17.84 kilowatt-hours and 12.84 kg of carbon equivalent, while eliminating paper waste entirely.">
      <div class="slide-header">
        <div class="kicker">Broader Impact</div>
        <div class="slide-title">SDG Alignment & Environmental Sustainability</div>
        <div class="slide-subtitle">Democratizing education with high compute efficiency and zero physical paper waste</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:12px;">
            <div class="card" style="border-left:4px solid var(--accent-blue);">
              <h3><span class="color-blue">SDG 4:</span> Quality Education (Target 4.4)</h3>
              <p>Provides adaptive, individualized computer science education at zero marginal cost, democratizing personalized tutoring for aspiring engineers.</p>
            </div>
            <div class="card" style="border-left:4px solid var(--accent-emerald);">
              <h3><span class="color-emerald">SDG 8 & 9:</span> Decent Work & Innovation</h3>
              <p>Accelerates student workforce readiness in software engineering through objective rubric-based coding retention.</p>
            </div>
            <div class="card" style="border-left:4px solid var(--accent-cyan);">
              <h3>Green Software Engineering</h3>
              <p>Lightweight WebGL client rendering offloads server CPU load. Zero paper flashcards generated.</p>
            </div>
          </div>

          <div class="card card-highlight" style="display:flex; flex-direction:column; justify-content:center;">
            <h3 style="margin-bottom:14px;">Lifecycle Environmental Footprint</h3>
            <table class="academic-table">
              <tbody>
                <tr>
                  <td>Development Electricity</td>
                  <td><b>17.84 kWh</b></td>
                </tr>
                <tr>
                  <td>Total Carbon Footprint</td>
                  <td><b>12.84 kg CO₂e</b></td>
                </tr>
                <tr>
                  <td>Paper Flashcard Savings</td>
                  <td><b>~4,500 Sheets Saved</b></td>
                </tr>
                <tr>
                  <td>Total Project Budget</td>
                  <td><b>₹10,200</b></td>
                </tr>
              </tbody>
            </table>
            <div style="margin-top:16px; font-size:0.8rem; color:var(--text-muted); line-height:1.4;">
              *Energy verified through hardware telemetry during development & benchmark cycles.
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 10: CONCLUSION & DEFENSE -->
    <section class="slide" data-title="Conclusion & Defense" data-speaker="Prasad"
      data-notes="In conclusion, SynapseFlow successfully overcomes the limitations of atomic flashcards by unifying Knowledge Graphs, Free Spaced Repetition Scheduling, and Socratic AI. We have demonstrated a 77.5% reduction in study workload, an 86 to 97% reduction in forgetting lapses, and superior predictive calibration on official benchmarks. We thank our guide Dr. Arti Mohanpurkar and the panel for their time, and we are now open for questions.">
      <div class="slide-header">
        <div class="kicker">Conclusion & Future Work</div>
        <div class="slide-title">Project Summary & Defense Readiness</div>
        <div class="slide-subtitle">Transforming cognitive retention into an interconnected science</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:14px;">
            <div class="card card-highlight">
              <h3>Key Research Deliverables</h3>
              <ul style="margin-left:18px; margin-top:8px; font-size:0.9rem; line-height:1.6; color:var(--text-secondary);">
                <li>Multi-Concept Graph Stability Propagation formulation ($\Delta S_v = \alpha w_{uv} \Delta S_u$).</li>
                <li>Monaco + Socratic AI integration replacing subjective human self-assessments.</li>
                <li>Comprehensive empirical evaluation proving 19.4% RMSE accuracy gain over FSRS.</li>
              </ul>
            </div>
            <div class="card">
              <h3>Future Scope</h3>
              <p>Federated graph personalization across student cohorts, multi-modal speech-based oral viva evaluation, and automated curriculum ingestion from GitHub codebases.</p>
            </div>
          </div>

          <div style="background:linear-gradient(135deg, rgba(30,58,138,0.3) 0%, rgba(88,28,135,0.2) 100%); border:1px solid var(--border-highlight); border-radius:var(--radius-md); padding:28px; text-align:center; display:flex; flex-direction:column; justify-content:center; align-items:center;">
            <div style="width:54px; height:54px; border-radius:50%; background:var(--grad-primary); display:flex; align-items:center; justify-content:center; font-size:1.6rem; margin-bottom:14px; box-shadow:0 0 25px rgba(59,130,246,0.5);">
              🎓
            </div>
            <h2 style="font-size:1.8rem; font-weight:800; margin-bottom:8px;">Thank You!</h2>
            <p style="color:var(--text-secondary); font-size:0.95rem; max-width:320px; line-height:1.5; margin-bottom:16px;">
              We are now open for Viva Voce questions and technical discussion.
            </p>
            <div style="display:flex; gap:8px;">
              <span class="badge badge-blue">Department of CSE</span>
              <span class="badge badge-emerald">MIT Chhatrapati Sambhajinagar</span>
            </div>
          </div>
        </div>
      </div>
    </section>

  </div>
</div>

<!-- SPEAKER NOTES DRAWER -->
<div class="speaker-drawer" id="speakerDrawer">
  <div class="speaker-drawer-header">
    <div class="speaker-drawer-title">
      <span>🎙️ SPEAKER NOTES & SCRIPT</span>
      <span class="badge badge-blue" id="speakerNameBadge">Prasad</span>
    </div>
    <button class="btn-ctrl" onclick="toggleSpeakerDrawer()" style="padding:3px 8px; font-size:0.75rem;">✕ Close (N)</button>
  </div>
  <div class="speaker-notes-content" id="speakerNotesText">
    Select a slide to view speaker notes.
  </div>
</div>

<!-- BOTTOM CONTROL BAR -->
<div class="deck-controls">
  <div class="controls-left">
    <button class="btn-ctrl" onclick="prevSlide()" title="Previous Slide (Left Arrow)">◀ Prev</button>
    <button class="btn-ctrl" onclick="nextSlide()" title="Next Slide (Right Arrow, Space)">Next ▶</button>
    <div class="slide-counter">
      Slide <span id="currentSlideNum">1</span> / <span id="totalSlideNum">10</span>
    </div>
  </div>

  <div class="progress-bar-container">
    <div class="progress-bar-fill" id="progressBar"></div>
  </div>

  <div class="controls-right">
    <button class="btn-ctrl" id="btnNotes" onclick="toggleSpeakerDrawer()" title="Toggle Speaker Script (Key: N or S)">
      📝 Speaker Notes
    </button>
    <button class="btn-ctrl" id="btnFullscreen" onclick="toggleFullscreen()" title="Toggle Fullscreen (Key: F)">
      ⛶ Fullscreen
    </button>
  </div>
</div>

<script>
  let currentSlideIndex = 0;
  const slides = document.querySelectorAll('.slide');
  const totalSlides = slides.length;
  const currentSlideNumEl = document.getElementById('currentSlideNum');
  const totalSlideNumEl = document.getElementById('totalSlideNum');
  const progressBarEl = document.getElementById('progressBar');
  const speakerDrawer = document.getElementById('speakerDrawer');
  const speakerNotesText = document.getElementById('speakerNotesText');
  const speakerNameBadge = document.getElementById('speakerNameBadge');
  const btnNotes = document.getElementById('btnNotes');

  totalSlideNumEl.textContent = totalSlides;

  function updateSlide(newIndex) {
    if (newIndex < 0 || newIndex >= totalSlides) return;
    
    slides[currentSlideIndex].classList.remove('active');
    currentSlideIndex = newIndex;
    slides[currentSlideIndex].classList.add('active');

    // Update Counter & Progress
    currentSlideNumEl.textContent = currentSlideIndex + 1;
    const progressPercent = ((currentSlideIndex + 1) / totalSlides) * 100;
    progressBarEl.style.width = progressPercent + '%';

    // Update Speaker Notes
    const activeSlide = slides[currentSlideIndex];
    const notes = activeSlide.getAttribute('data-notes') || 'No notes for this slide.';
    const speaker = activeSlide.getAttribute('data-speaker') || 'Presenter';
    speakerNotesText.innerHTML = notes;
    speakerNameBadge.textContent = 'Speaker: ' + speaker;
  }

  function nextSlide() {
    if (currentSlideIndex < totalSlides - 1) {
      updateSlide(currentSlideIndex + 1);
    }
  }

  function prevSlide() {
    if (currentSlideIndex > 0) {
      updateSlide(currentSlideIndex - 1);
    }
  }

  function toggleSpeakerDrawer() {
    speakerDrawer.classList.toggle('open');
    btnNotes.classList.toggle('active-ctrl');
  }

  function toggleFullscreen() {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(err => {
        alert(`Error attempting to enable fullscreen: ${err.message}`);
      });
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
    }
  }

  // Keyboard navigation
  window.addEventListener('keydown', (e) => {
    switch (e.key) {
      case 'ArrowRight':
      case ' ':
      case 'PageDown':
        nextSlide();
        break;
      case 'ArrowLeft':
      case 'PageUp':
        prevSlide();
        break;
      case 'n':
      case 'N':
      case 's':
      case 'S':
        toggleSpeakerDrawer();
        break;
      case 'f':
      case 'F':
        toggleFullscreen();
        break;
      case 'Escape':
        if (speakerDrawer.classList.contains('open')) {
          toggleSpeakerDrawer();
        }
        break;
    }
  });

  // Initial load
  updateSlide(0);
</script>
</body>
</html>
"""

with open("presentation/index.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print("Generated presentation/index.html successfully!")
