# -*- coding: utf-8 -*-
"""
Generates the Academic-Themed HTML/CSS/JS presentation for SynapseFlow.
Designed to look like a prestigious University / IEEE / LaTeX Beamer presentation:
- Ivory & Oxford Navy academic palette
- Classic Serif academic typography (Playfair / Georgia / Latin Modern)
- Formal LaTeX-style formula blocks, definition cards, and booktabs tables
- Full-bleed diagram containers with figures from report_assets
- Interactive keyboard navigation (Arrows, F for fullscreen, N/S for speaker script)
- Full word-for-word academic defense script embedded per slide
"""

academic_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SynapseFlow: Academic Defense Presentation</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700;800&family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-page: #f4f1eb;
    --bg-slide: #ffffff;
    --bg-subtle: #fbf9f5;
    --bg-card: #ffffff;
    --border-main: #dcd6cd;
    --border-dark: #1e293b;
    --border-light: #ece7df;
    
    --navy-primary: #1a365d;     /* Oxford Academic Navy */
    --navy-deep: #0f172a;
    --crimson: #881337;         /* Academic Burgundy / Seal */
    --gold: #b45309;            /* Academic Ochre / Gold */
    --forest: #14532d;          /* Academic Forest Green */
    
    --text-primary: #0f172a;
    --text-secondary: #334155;
    --text-muted: #64748b;
    
    --font-serif: 'Lora', Georgia, 'Times New Roman', serif;
    --font-title: 'Cinzel', 'Lora', Georgia, serif;
    --font-sans: 'Plus Jakarta Sans', system-ui, sans-serif;
    --font-mono: 'JetBrains Mono', Consolas, monospace;
    
    --shadow-slide: 0 20px 40px -15px rgba(15, 23, 42, 0.15), 0 0 1px 1px rgba(15, 23, 42, 0.05);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background-color: var(--bg-page);
    color: var(--text-primary);
    font-family: var(--font-sans);
    height: 100vh;
    overflow: hidden;
    user-select: none;
    display: flex;
    flex-direction: column;
  }

  /* Presentation Viewport */
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
    max-width: 1340px;
    aspect-ratio: 16 / 9;
    max-height: calc(100vh - 90px);
    background-color: var(--bg-slide);
    border: 1px solid var(--border-main);
    box-shadow: var(--shadow-slide);
    position: relative;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  /* Academic Slide Paper Styling */
  .slide {
    position: absolute;
    inset: 0;
    padding: 38px 52px;
    display: flex;
    flex-direction: column;
    opacity: 0;
    pointer-events: none;
    transform: translateY(8px);
    transition: opacity 0.3s ease, transform 0.3s ease;
    background: #ffffff;
  }

  .slide.active {
    opacity: 1;
    pointer-events: auto;
    transform: translateY(0);
    z-index: 2;
  }

  /* Formal Academic Header */
  .slide-header {
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1.5px solid var(--border-main);
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    flex-shrink: 0;
  }
  .header-left {
    flex: 1;
  }
  .kicker {
    font-family: var(--font-mono);
    font-size: 0.76rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--navy-primary);
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .kicker::before {
    content: "§";
    color: var(--crimson);
    font-size: 0.95rem;
    font-weight: 700;
  }
  .slide-title {
    font-family: var(--font-serif);
    font-size: 1.95rem;
    font-weight: 700;
    color: var(--navy-deep);
    letter-spacing: -0.015em;
    line-height: 1.2;
  }
  .slide-subtitle {
    font-size: 0.9rem;
    color: var(--text-muted);
    margin-top: 3px;
    font-style: italic;
  }
  .header-badge {
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--text-muted);
    border: 1px solid var(--border-main);
    padding: 4px 10px;
    background: var(--bg-subtle);
    border-radius: 2px;
  }

  /* Content Body */
  .slide-body {
    flex: 1;
    display: flex;
    gap: 28px;
    min-height: 0;
    align-items: center;
  }
  .grid-2col {
    display: grid;
    grid-template-columns: 1.05fr 1fr;
    gap: 26px;
    width: 100%;
    height: 100%;
    align-items: center;
  }
  .grid-3col {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 18px;
    width: 100%;
    height: 100%;
    align-items: center;
  }

  /* Academic Cards & Boxes */
  .academic-card {
    background: var(--bg-card);
    border: 1px solid var(--border-main);
    border-radius: 4px;
    padding: 16px 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
  }
  .academic-card.card-accent {
    border-left: 4px solid var(--navy-primary);
    background: #fdfefe;
  }
  .academic-card.card-crimson {
    border-left: 4px solid var(--crimson);
    background: #fffafa;
  }
  .academic-card.card-forest {
    border-left: 4px solid var(--forest);
    background: #fbfdfb;
  }
  .academic-card h3 {
    font-family: var(--font-serif);
    font-size: 1.05rem;
    font-weight: 700;
    color: var(--navy-deep);
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .academic-card p {
    font-size: 0.86rem;
    line-height: 1.55;
    color: var(--text-secondary);
  }

  /* Formal Formula & Theorem Block */
  .theorem-box {
    background: #f8fafc;
    border: 1px solid #cbd5e1;
    border-left: 4px solid var(--navy-primary);
    padding: 14px 18px;
    border-radius: 2px;
    margin: 8px 0;
  }
  .theorem-header {
    font-family: var(--font-serif);
    font-size: 0.84rem;
    font-weight: 700;
    color: var(--navy-primary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
  }
  .formula-display {
    font-family: var(--font-serif);
    font-size: 1.05rem;
    font-style: italic;
    color: var(--navy-deep);
    text-align: center;
    padding: 8px 0;
    border-top: 1px dashed #e2e8f0;
    border-bottom: 1px dashed #e2e8f0;
    margin: 6px 0;
    background: #ffffff;
  }
  .formula-caption {
    font-size: 0.78rem;
    color: var(--text-muted);
    line-height: 1.4;
  }

  /* Academic Stat Badges */
  .stat-deck {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
    width: 100%;
  }
  .stat-block {
    background: var(--bg-subtle);
    border: 1px solid var(--border-main);
    border-top: 3px solid var(--navy-primary);
    padding: 12px 14px;
    text-align: center;
    border-radius: 2px;
  }
  .stat-num {
    font-family: var(--font-serif);
    font-size: 1.9rem;
    font-weight: 700;
    color: var(--navy-primary);
    line-height: 1.1;
  }
  .stat-lbl {
    font-size: 0.72rem;
    font-family: var(--font-mono);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-muted);
    margin-top: 4px;
    font-weight: 600;
  }

  /* Booktabs Formal Academic Table */
  .booktabs-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.84rem;
    text-align: left;
    margin: 6px 0;
  }
  .booktabs-table th {
    border-top: 2px solid var(--border-dark);
    border-bottom: 1px solid var(--border-dark);
    padding: 8px 10px;
    font-family: var(--font-serif);
    font-weight: 700;
    color: var(--navy-deep);
    background: #faf8f5;
  }
  .booktabs-table td {
    padding: 7px 10px;
    border-bottom: 1px solid var(--border-light);
    color: var(--text-secondary);
  }
  .booktabs-table tr:last-child td {
    border-bottom: 2px solid var(--border-dark);
  }
  .booktabs-table tr.highlight-academic {
    background: #f1f5f9;
    font-weight: 600;
  }
  .booktabs-table tr.highlight-academic td {
    color: var(--navy-primary);
  }

  /* Formal Diagram Framing */
  .diagram-frame {
    width: 100%;
    height: 100%;
    max-height: 380px;
    background: #ffffff;
    border: 1px solid var(--border-main);
    padding: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    box-shadow: inset 0 0 0 1px rgba(0,0,0,0.02);
    position: relative;
  }
  .diagram-frame img {
    max-width: 100%;
    max-height: calc(100% - 24px);
    object-fit: contain;
  }
  .diagram-caption {
    font-family: var(--font-serif);
    font-size: 0.76rem;
    font-style: italic;
    color: var(--text-muted);
    text-align: center;
    margin-top: 6px;
    width: 100%;
    border-top: 1px solid var(--border-light);
    padding-top: 4px;
  }

  /* Bottom Controls Toolbar */
  .deck-controls {
    height: 54px;
    background: #ffffff;
    border-top: 1px solid var(--border-main);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 28px;
    z-index: 10;
  }
  .btn-academic {
    background: #ffffff;
    border: 1px solid var(--border-main);
    color: var(--text-primary);
    padding: 6px 14px;
    font-family: var(--font-sans);
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    border-radius: 2px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    transition: background 0.15s, border-color 0.15s;
  }
  .btn-academic:hover {
    background: var(--bg-subtle);
    border-color: var(--border-dark);
  }
  .btn-academic.active-btn {
    background: var(--navy-primary);
    color: #ffffff;
    border-color: var(--navy-primary);
  }

  .slide-counter {
    font-family: var(--font-mono);
    font-size: 0.82rem;
    color: var(--text-muted);
  }
  .slide-counter span {
    font-weight: 700;
    color: var(--navy-deep);
  }

  .progress-track {
    flex: 1;
    max-width: 260px;
    height: 3px;
    background: var(--border-light);
    position: relative;
  }
  .progress-fill {
    height: 100%;
    width: 10%;
    background: var(--navy-primary);
    transition: width 0.3s ease;
  }

  /* Speaker Notes Drawer (Academic Parchment Style) */
  .speaker-drawer {
    position: fixed;
    bottom: 54px;
    left: 0;
    right: 0;
    background: #fdfbf7;
    border-top: 2px solid var(--navy-primary);
    padding: 22px 36px;
    max-height: 230px;
    overflow-y: auto;
    transform: translateY(100%);
    transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    z-index: 9;
    box-shadow: 0 -8px 25px rgba(0, 0, 0, 0.08);
  }
  .speaker-drawer.open {
    transform: translateY(0);
  }
  .speaker-drawer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
    border-bottom: 1px solid var(--border-main);
    padding-bottom: 6px;
  }
  .speaker-title {
    font-family: var(--font-serif);
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--navy-primary);
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .speaker-content {
    font-family: var(--font-serif);
    font-size: 0.96rem;
    line-height: 1.65;
    color: var(--text-primary);
  }
  .speaker-content b {
    color: var(--navy-primary);
  }
  .speaker-tag {
    font-family: var(--font-mono);
    font-size: 0.74rem;
    background: #e2e8f0;
    padding: 2px 8px;
    border-radius: 2px;
    color: var(--navy-deep);
  }
</style>
</head>
<body>

<div class="viewport-wrapper">
  <div class="slide-container" id="slideDeck">

    <!-- SLIDE 1: FORMAL COVER / TITLE -->
    <section class="slide active" data-title="Title & Accreditations" data-speaker="Prasad Anil Kankhar"
      data-notes="Respected members of the review committee and our research guide Dr. Arti Mohanpurkar. Good morning. We present our Major Project-II defense titled SYNAPSEFLOW: An Adaptive Multi-Concept Knowledge Graph and Socratic AI-Powered Spaced Repetition System. This work was conducted at the Department of Computer Science and Engineering, Maharashtra Institute of Technology, Chhatrapati Sambhajinagar, affiliated to Dr. Babasaheb Ambedkar Marathwada University. Our team members are Prasad Anil Kankhar, Prashant Anil Gande, and Aditya Devidas Kavde.">
      <div style="height:100%; display:flex; flex-direction:column; justify-content:space-between;">
        
        <!-- University Crest Header -->
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1.5px solid var(--border-main); padding-bottom:12px;">
          <div style="display:flex; align-items:center; gap:16px;">
            <img src="../report_assets/mit_csn_logo.png" alt="MIT CSN Logo" style="height:44px; object-fit:contain;">
            <div>
              <div style="font-family:var(--font-title); font-size:0.88rem; font-weight:700; letter-spacing:0.04em; color:var(--navy-deep);">
                MAHARASHTRA INSTITUTE OF TECHNOLOGY, CHHATRAPATI SAMBHAJINAGAR
              </div>
              <div style="font-size:0.75rem; color:var(--text-muted); font-style:italic;">
                Affiliated to Dr. Babasaheb Ambedkar Marathwada University · Department of Computer Science & Engineering
              </div>
            </div>
          </div>
          <div class="header-badge">Academic Year 2026–2027</div>
        </div>

        <!-- Project Title Banner -->
        <div style="margin: 22px 0; text-align:center;">
          <div style="font-family:var(--font-mono); font-size:0.8rem; font-weight:600; text-transform:uppercase; letter-spacing:0.15em; color:var(--crimson); margin-bottom:8px;">
            Bachelor of Technology · Major Project-II Defense
          </div>
          <h1 style="font-family:var(--font-serif); font-size:2.35rem; font-weight:700; color:var(--navy-primary); line-height:1.2; margin-bottom:10px;">
            SYNAPSEFLOW
          </h1>
          <h2 style="font-family:var(--font-serif); font-size:1.15rem; font-weight:500; font-style:italic; color:var(--text-secondary); max-width:920px; margin:0 auto; line-height:1.45;">
            An Adaptive Multi-Concept Knowledge Graph and Socratic AI-Powered Spaced Repetition System
          </h2>
        </div>

        <!-- Candidate & Guide Box -->
        <div style="display:grid; grid-template-columns: 1.8fr 1.2fr; gap:20px; background:var(--bg-subtle); border:1px solid var(--border-main); padding:16px 22px; border-radius:2px;">
          <div>
            <div style="font-family:var(--font-mono); font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted); margin-bottom:6px; font-weight:700;">
              Student Candidates
            </div>
            <div style="display:flex; flex-direction:column; gap:3px; font-size:0.86rem; color:var(--navy-deep);">
              <div><b>Prasad Anil Kankhar</b> <span style="font-family:var(--font-mono); font-size:0.78rem; color:var(--text-muted);">(Roll No: BT42036)</span></div>
              <div><b>Prashant Anil Gande</b> <span style="font-family:var(--font-mono); font-size:0.78rem; color:var(--text-muted);">(Roll No: BT42002)</span></div>
              <div><b>Aditya Devidas Kavde</b> <span style="font-family:var(--font-mono); font-size:0.78rem; color:var(--text-muted);">(Roll No: BT42043)</span></div>
            </div>
          </div>
          <div style="border-left:1px solid var(--border-main); padding-left:20px;">
            <div style="font-family:var(--font-mono); font-size:0.72rem; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-muted); margin-bottom:6px; font-weight:700;">
              Supervision & Approval
            </div>
            <div style="font-size:0.86rem; color:var(--navy-deep);">
              Guide: <b>Dr. Arti Mohanpurkar</b>
            </div>
            <div style="font-size:0.78rem; color:var(--text-muted); margin-top:2px;">
              Head of Department: <b>Dr. Smita Kasar</b>
            </div>
            <div style="font-size:0.78rem; color:var(--text-muted); margin-top:2px;">
              Director: <b>Dr. N. G. Patil</b>
            </div>
          </div>
        </div>

      </div>
    </section>

    <!-- SLIDE 2: PROBLEM DEFINITION -->
    <section class="slide" data-title="Problem Definition & Motivation" data-speaker="Prasad Anil Kankhar"
      data-notes="Traditional Spaced Repetition algorithms such as SuperMemo SM-2 and Anki have modeled human memory decay under the assumption of concept independence. In technical computer science domains, concepts are intrinsically hierarchical and interdependent. When a student fails a prerequisite concept, isolated schedulers fail to propagate that degradation, resulting in severe cascading forgetting lapses. Furthermore, existing self-grading interfaces rely on four subjective heuristic buttons—Again, Hard, Good, and Easy—which introduce significant metacognitive bias and provide zero semantic feedback on implementation correctness.">
      <div class="slide-header">
        <div class="header-left">
          <div class="kicker">Chapter 1 · Theoretical Motivation</div>
          <div class="slide-title">Theoretical Limitations of Classical SRS</div>
          <div class="slide-subtitle">The failure of scalar independent memory models in hierarchical engineering curricula</div>
        </div>
        <div class="header-badge">Formulation</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:12px;">
            <div class="academic-card card-crimson">
              <h3>I. Concept Independence Assumption</h3>
              <p>Classical models (SM-2, Leitner) assume memory traces are mutually orthogonal: $S_i \perp S_j$. In Computer Science, failing a fundamental prerequisite like <i>Recursion</i> invalidates retention in <i>Dynamic Programming</i>, yet isolated cards remain scheduled as if stable.</p>
            </div>
            <div class="academic-card card-crimson">
              <h3>II. Metacognitive Grading Bias</h3>
              <p>Subjective self-rating (<i>Again, Hard, Good, Easy</i>) suffers from severe human miscalibration and Dunning-Kruger overconfidence. Students receive no diagnostic insight into syntax errors, time complexity, or edge cases.</p>
            </div>
            <div class="academic-card card-accent">
              <h3>III. Proposed Paradigm Shift</h3>
              <p>SynapseFlow models human technical retention across a <b>Directed Knowledge Graph $\mathcal{G}=(V, E)$</b> with asymmetric memory stability propagation and real-time Socratic code validation.</p>
            </div>
          </div>
          <div class="diagram-frame">
            <img src="../report_assets/diagrams/fig1_1_isolated_vs_graph.png" alt="Isolated Flashcards vs Knowledge Graph SRS">
            <div class="diagram-caption">Figure 1.1: Topological comparison of isolated scalar cards versus interconnected knowledge graph memory.</div>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 3: SYSTEM ARCHITECTURE -->
    <section class="slide" data-title="System Architecture" data-speaker="Prashant Anil Gande"
      data-notes="The SynapseFlow framework is structured into three primary architectural tiers: First, a persistent Knowledge Graph layer mapping curriculum dependencies into directed synaptic vertices. Second, the Multi-Concept Free Spaced Repetition Scheduling engine executing dynamic asymmetric stability updates. Third, an integrated Socratic AI code evaluation service embedded within the Monaco Editor. Upon answer evaluation, the stability delta is computed and propagated across adjacent prerequisite and successor nodes.">
      <div class="slide-header">
        <div class="header-left">
          <div class="kicker">Chapter 3 · System Design</div>
          <div class="slide-title">High-Level Architectural Framework</div>
          <div class="slide-subtitle">Tripartite integration of knowledge topology, memory modeling, and Socratic evaluation</div>
        </div>
        <div class="header-badge">HLD Architecture</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:12px;">
            <div class="academic-card card-accent">
              <h3>Pillar 1: Directed Knowledge Graph Topology</h3>
              <p>Curriculum concepts are formalized as vertices $V$. Dependencies and prerequisite structures are represented as weighted directed edges $E$ supporting sublinear $\mathcal{O}(|V|+|E|)$ graph traversal.</p>
            </div>
            <div class="academic-card card-accent">
              <h3>Pillar 2: Multi-Concept FSRS Engine</h3>
              <p>Extends the Free Spaced Repetition Scheduler (FSRS v4.5) to propagate stability deltas across 1-hop topological neighbors, actively shielding against prerequisite degradation.</p>
            </div>
            <div class="academic-card card-accent">
              <h3>Pillar 3: Socratic Program Evaluator</h3>
              <p>Replaces subjective buttons with an embedded Monaco code studio. Submissions are objectively scored against algorithmic rubrics, returning step-by-step Socratic hints.</p>
            </div>
          </div>
          <div class="diagram-frame">
            <img src="../report_assets/diagrams/fig3_1_system_architecture.png" alt="High Level System Architecture">
            <div class="diagram-caption">Figure 3.1: High-Level System Architecture and end-to-end data processing workflow.</div>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 4: MATHEMATICAL MODEL -->
    <section class="slide" data-title="Mathematical Formulation" data-speaker="Prashant Anil Gande"
      data-notes="Our mathematical model introduces two novel formulations. First, the Synaptic Edge Weight formula fuses three independent cognitive signals: semantic cosine embedding similarity, pedagogical prerequisite tree depth, and empirical co-failure conditional probability. Second, the Graph Stability Propagation equation calculates the stability update for adjacent nodes using asymmetric propagation factors: alpha_pass equals 0.05 for conservative forward reinforcement, while alpha_fail equals 0.15 for aggressive backward prerequisite shielding.">
      <div class="slide-header">
        <div class="header-left">
          <div class="kicker">Chapter 3 · Mathematical Formulation</div>
          <div class="slide-title">Synaptic Weighting & Dynamic Stability Propagation</div>
          <div class="slide-subtitle">Formulating human memory dynamics across hierarchical conceptual graphs</div>
        </div>
        <div class="header-badge">Algorithms</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:10px;">
            <div class="theorem-box">
              <div class="theorem-header">Equation 1: Multi-Signal Synaptic Weight Fusion</div>
              <div class="formula-display">
                w_{uv} = \lambda_{sem} \cdot S_{sem}(u,v) + \lambda_{ped} \cdot W_{ped}(u,v) + \lambda_{data} \cdot P(fail_v \mid fail_u)
              </div>
              <div class="formula-caption">
                Parametric weights: $\lambda_{sem}=0.35$ (semantic embeddings), $\lambda_{ped}=0.45$ (curriculum depth), $\lambda_{data}=0.20$ (historical co-failure probability).
              </div>
            </div>

            <div class="theorem-box">
              <div class="theorem-header">Equation 2: Asymmetric Stability Propagation</div>
              <div class="formula-display">
                \Delta S_v = \alpha \cdot w_{uv} \cdot \Delta S_u
              </div>
              <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; margin-top:6px;">
                <div style="background:#f0fdf4; border:1px solid #bbf7d0; padding:6px 10px; border-radius:2px;">
                  <b style="color:var(--forest); font-family:var(--font-mono); font-size:0.8rem;">\alpha_{pass} = 0.05</b>
                  <div style="font-size:0.72rem; color:var(--text-muted);">Conservative forward reinforcement</div>
                </div>
                <div style="background:#fff1f2; border:1px solid #fecdd3; padding:6px 10px; border-radius:2px;">
                  <b style="color:var(--crimson); font-family:var(--font-mono); font-size:0.8rem;">\alpha_{fail} = 0.15</b>
                  <div style="font-size:0.72rem; color:var(--text-muted);">Aggressive backward penalty (3:1 ratio)</div>
                </div>
              </div>
            </div>
          </div>
          <div class="diagram-frame">
            <img src="../report_assets/diagrams/fig2_1_multi_signal_weight.png" alt="Multi-Signal Weighting Scheme">
            <div class="diagram-caption">Figure 2.1: Tri-signal weight synthesis and asymmetric stability propagation mechanism.</div>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 5: IMPLEMENTATION PIPELINE -->
    <section class="slide" data-title="Implementation & Software Stack" data-speaker="Prashant Anil Gande"
      data-notes="The implementation pipeline utilizes a high-performance, modular full-stack architecture. The presentation layer is developed in React 18 with WebGL Canvas rendering force-directed graphs client-side at 60 FPS. The service layer is powered by Python FastAPI and NetworkX, delivering sublinear traversal latency under 25 milliseconds. Submissions in the Monaco editor are objectively graded by an embedded LLM evaluation service with structured prompt templates and response caching.">
      <div class="slide-header">
        <div class="header-left">
          <div class="kicker">Chapter 3 · Software Implementation</div>
          <div class="slide-title">Modular Full-Stack Software Pipeline</div>
          <div class="slide-subtitle">Engineered for client-side WebGL acceleration and sub-25ms backend graph traversal</div>
        </div>
        <div class="header-badge">LLD Pipeline</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:12px;">
            <div class="academic-card card-accent">
              <h3>Presentation Layer (Client-Side)</h3>
              <p><b>React 18 + Vite + Tailwind CSS</b>. Force-directed 3D/2D topological rendering implemented via WebGL Canvas (<span style="font-family:var(--font-mono); font-size:0.78rem;">react-force-graph-2d</span>), offloading compute from the server.</p>
            </div>
            <div class="academic-card card-accent">
              <h3>Service & Scheduling Layer</h3>
              <p><b>FastAPI + NetworkX Engine</b>. Asynchronous REST endpoints processing BFS 1-hop topological updates with sub-25 millisecond execution latency.</p>
            </div>
            <div class="academic-card card-accent">
              <h3>Evaluation & Persistence Layer</h3>
              <p><b>Monaco Code IDE + SQLite/PostgreSQL</b>. SQLite configured with Write-Ahead Logging (WAL) and foreign keys, supporting seamless zero-install portable deployment.</p>
            </div>
          </div>
          <div class="diagram-frame">
            <img src="../report_assets/diagrams/fig3_3_propagation_flowchart.png" alt="Low Level Propagation Flowchart">
            <div class="diagram-caption">Figure 3.3: Low-level procedural execution flowchart for stability delta propagation.</div>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 6: CONTROLLED BENCHMARK -->
    <section class="slide" data-title="Controlled Simulation Benchmark" data-speaker="Aditya Devidas Kavde"
      data-notes="We evaluated SynapseFlow against standard FSRS v4.5 and the baseline SM-2 algorithm through a 90-day simulated semester curriculum across 100 hierarchical concepts, comprising 1,065 study sessions. SynapseFlow reduced total review workload by 77.5%, requiring only 633 reviews compared to 2,817 in SM-2. Crucially, forgetting lapses were slashed by 97.0% down to 46 lapses, while maintaining an overall target retention of 95.30%.">
      <div class="slide-header">
        <div class="header-left">
          <div class="kicker">Chapter 4 · Empirical Validation</div>
          <div class="slide-title">90-Day Controlled Curriculum Simulation</div>
          <div class="slide-subtitle">Workload and lapse suppression across 100 interconnected Computer Science concepts</div>
        </div>
        <div class="header-badge">Benchmark 1</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:14px;">
            <div class="stat-deck">
              <div class="stat-block">
                <div class="stat-num" style="color:var(--forest);">-77.5%</div>
                <div class="stat-lbl">Review Workload</div>
              </div>
              <div class="stat-block">
                <div class="stat-num" style="color:var(--navy-primary);">46</div>
                <div class="stat-lbl">Lapses (vs 1,525)</div>
              </div>
              <div class="stat-block">
                <div class="stat-num" style="color:var(--gold);">95.3%</div>
                <div class="stat-lbl">Target Retention</div>
              </div>
            </div>

            <table class="booktabs-table">
              <thead>
                <tr>
                  <th>Algorithm</th>
                  <th>Total Reviews</th>
                  <th>Forgetting Lapses</th>
                  <th>Mean Retention</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>SuperMemo SM-2 (Baseline)</td>
                  <td>2,817</td>
                  <td>1,525</td>
                  <td>90.2%</td>
                </tr>
                <tr>
                  <td>FSRS v4.5 (Standalone)</td>
                  <td>1,091</td>
                  <td>329</td>
                  <td>94.1%</td>
                </tr>
                <tr class="highlight-academic">
                  <td><b>SynapseFlow (Proposed)</b></td>
                  <td><b>633</b></td>
                  <td><b>46</b></td>
                  <td><b>95.3%</b></td>
                </tr>
              </tbody>
            </table>

            <div class="academic-card card-forest" style="padding:10px 14px;">
              <p style="font-size:0.8rem;"><b>Empirical Deduction:</b> Asymmetric backward propagation aggressively suppresses cascade failures, eliminating over 1,400 unnecessary review interventions.</p>
            </div>
          </div>
          <div class="diagram-frame">
            <img src="../report_assets/diagrams/fig4_1_workload_benchmark.png" alt="Workload Benchmark Comparison">
            <div class="diagram-caption">Figure 4.1: Comparative workload and lapse frequency trajectory across the 90-day simulation.</div>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 7: OFFICIAL SRS BENCHMARK -->
    <section class="slide" data-title="Official SRS Benchmark Telemetry" data-speaker="Aditya Devidas Kavde"
      data-notes="Next, we evaluated SynapseFlow on the official open Spaced Repetition Benchmark using empirical real-student telemetry comprising 600 reviews across 165 concepts and 582 graph edges. SynapseFlow demonstrated superior calibration and predictive accuracy, achieving the lowest Log Loss at 0.5062, the highest AUC at 0.5783, and an RMSE of 0.1059—a 19.4% error reduction over standard FSRS and a 74.6% error reduction over legacy SM-2.">
      <div class="slide-header">
        <div class="header-left">
          <div class="kicker">Chapter 4 · Open Benchmark Telemetry</div>
          <div class="slide-title">Official SRS Benchmark & Telemetry Evaluation</div>
          <div class="slide-subtitle">Evaluated on real student logs across 165 concepts and 582 topological graph edges</div>
        </div>
        <div class="header-badge">Benchmark 2</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:14px;">
            <div class="stat-deck">
              <div class="stat-block">
                <div class="stat-num" style="color:var(--forest);">0.5062</div>
                <div class="stat-lbl">Log Loss (Lowest)</div>
              </div>
              <div class="stat-block">
                <div class="stat-num" style="color:var(--navy-primary);">0.1059</div>
                <div class="stat-lbl">20-Bin RMSE</div>
              </div>
              <div class="stat-block">
                <div class="stat-num" style="color:var(--crimson);">+19.4%</div>
                <div class="stat-lbl">FSRS Error Reduction</div>
              </div>
            </div>

            <table class="booktabs-table">
              <thead>
                <tr>
                  <th>Model Architecture</th>
                  <th>Log Loss ↓</th>
                  <th>RMSE (20-bin) ↓</th>
                  <th>AUC ↑</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>SuperMemo SM-2</td>
                  <td>0.6288</td>
                  <td>0.4172</td>
                  <td>0.5042</td>
                </tr>
                <tr>
                  <td>FSRS v4.5 (Isolated)</td>
                  <td>0.5642</td>
                  <td>0.1314</td>
                  <td>0.5312</td>
                </tr>
                <tr class="highlight-academic">
                  <td><b>SynapseFlow (Proposed)</b></td>
                  <td><b>0.5062</b></td>
                  <td><b>0.1059</b></td>
                  <td><b>0.5783</b></td>
                </tr>
              </tbody>
            </table>

            <div class="academic-card card-accent" style="padding:10px 14px;">
              <p style="font-size:0.8rem;"><b>Significance:</b> Real student learning trajectories follow non-linear graph topologies; graph-informed stability modeling substantially improves predictive retention calibration.</p>
            </div>
          </div>
          <div class="diagram-frame">
            <img src="../report_assets/diagrams/fig4_2_retention_efficiency.png" alt="Retention Efficiency Calibration">
            <div class="diagram-caption">Figure 4.2: Retention efficiency curve and calibration alignment across discrete review bins.</div>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 8: COST & FEASIBILITY -->
    <section class="slide" data-title="Cost Analysis & Feasibility" data-speaker="Prasad Anil Kankhar"
      data-notes="A comprehensive engineering cost analysis was carried out in Chapter 4.4. By executing graph operations client-side and using prompt token caching, cloud infrastructure costs were minimized. Over 10,000 coding evaluations, LLM token expenditure totaled ₹4,200, hardware amortization totaled ₹3,000, and domain/SSL and report binding totaled ₹3,000, yielding a total project cost of ₹10,200. This confirms high practical feasibility for university deployment.">
      <div class="slide-header">
        <div class="header-left">
          <div class="kicker">Chapter 4.4 · Engineering Feasibility</div>
          <div class="slide-title">Cost Estimation & Operational Feasibility</div>
          <div class="slide-subtitle">Economic assessment demonstrating minimal deployment and operational overhead</div>
        </div>
        <div class="header-badge">Cost Audit</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:12px;">
            <div class="academic-card card-accent">
              <h3>Zero-Marginal Client Architecture</h3>
              <p>Client-side WebGL graph rendering and local SQLite database execution completely eliminate recurring server CPU licensing costs.</p>
            </div>
            <div class="academic-card card-accent">
              <h3>LLM API Cost Mitigation</h3>
              <p>Automated input prompt compression and semantic response caching restrict token consumption to an average of ₹0.42 per complex programming evaluation.</p>
            </div>
            <div class="academic-card card-forest">
              <h3>Educational Viability</h3>
              <p>Provides institutional-grade personalized Socratic tutoring at less than 1% of the cost of commercial 1-on-1 human mentorship programs.</p>
            </div>
          </div>

          <div class="academic-card" style="padding:18px 22px;">
            <div style="font-family:var(--font-serif); font-size:1.05rem; font-weight:700; color:var(--navy-deep); margin-bottom:10px;">
              Table 4.3: Financial Resource Allocation
            </div>
            <table class="booktabs-table">
              <thead>
                <tr>
                  <th>Expense Component</th>
                  <th>Description</th>
                  <th>Amount (₹)</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Cloud Server & Hosting</td>
                  <td>Local / Serverless Tier</td>
                  <td>₹0</td>
                </tr>
                <tr>
                  <td>LLM Token Consumption</td>
                  <td>10,000 AI Evaluations</td>
                  <td>₹4,200</td>
                </tr>
                <tr>
                  <td>Hardware Amortization</td>
                  <td>Workstation & Telemetry</td>
                  <td>₹3,000</td>
                </tr>
                <tr>
                  <td>Domain, SSL & Binding</td>
                  <td>Documentation & Certification</td>
                  <td>₹3,000</td>
                </tr>
                <tr class="highlight-academic">
                  <td><b>Total Project Expenditure</b></td>
                  <td><b>Comprehensive Development</b></td>
                  <td><b>₹10,200</b></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 9: SDGS & ENVIRONMENT -->
    <section class="slide" data-title="SDGs & Environmental Impact" data-speaker="Prasad Anil Kankhar"
      data-notes="SynapseFlow is closely aligned with the United Nations Sustainable Development Goals. Under SDG 4, Target 4.4, it democratizes high-quality technical education, enabling equitable access to mastery learning. Under SDGs 8 and 9, it builds workforce-ready software engineering capabilities. From an environmental standpoint, our client-side WebGL architecture restricted lifecycle energy consumption to 17.84 kWh and 12.84 kg of CO2 equivalent, while entirely replacing physical paper flashcards.">
      <div class="slide-header">
        <div class="header-left">
          <div class="kicker">Appendix B · Sustainability Mapping</div>
          <div class="slide-title">Sustainable Development Goals & Environmental Impact</div>
          <div class="slide-subtitle">Academic alignment with UN SDG 4, 8, 9 and quantitative environmental footprint</div>
        </div>
        <div class="header-badge">SDG Compliance</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:10px;">
            <div class="academic-card card-accent">
              <h3>SDG 4: Quality Education (Target 4.4)</h3>
              <p>Equitable access to personalized technical mentorship, empowering engineering students across diverse socio-economic backgrounds with objective mastery tools.</p>
            </div>
            <div class="academic-card card-accent">
              <h3>SDG 8 & 9: Decent Work & Innovation</h3>
              <p>Fosters sustainable industrial innovation by bridging the gap between theoretical computer science curricula and rigorous industry-standard software skills.</p>
            </div>
            <div class="academic-card card-forest">
              <h3>Paperless Knowledge Representation</h3>
              <p>Eliminates physical index card production, saving an estimated 4,500 paper sheets per student over a four-year technical degree.</p>
            </div>
          </div>

          <div class="academic-card" style="padding:16px 20px;">
            <div style="font-family:var(--font-serif); font-size:1.0rem; font-weight:700; color:var(--navy-deep); margin-bottom:8px;">
              Table II.1: Environmental Resource Consumption Audit
            </div>
            <table class="booktabs-table">
              <thead>
                <tr>
                  <th>Resource Metric</th>
                  <th>Observed Value</th>
                  <th>Environmental Consequence</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Development Power</td>
                  <td><b>17.84 kWh</b></td>
                  <td>Optimized workstation compute</td>
                </tr>
                <tr>
                  <td>Carbon Footprint</td>
                  <td><b>12.84 kg CO₂e</b></td>
                  <td>Mitigated via WebGL client offloading</td>
                </tr>
                <tr>
                  <td>Paper Flashcard Savings</td>
                  <td><b>~4,500 Sheets</b></td>
                  <td>Zero pulp and ink consumption</td>
                </tr>
                <tr>
                  <td>Electronic Waste</td>
                  <td><b>0 units</b></td>
                  <td>Pure software deployment on existing PCs</td>
                </tr>
              </tbody>
            </table>
            <div style="font-size:0.75rem; color:var(--text-muted); font-style:italic; margin-top:6px;">
              *Values verified through hardware power telemetry during model calibration and benchmark simulations.
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- SLIDE 10: CONCLUSION & VIVA DEFENSE -->
    <section class="slide" data-title="Conclusion & Viva Voce Defense" data-speaker="Prasad Anil Kankhar"
      data-notes="In conclusion, SynapseFlow bridges the gap between spaced repetition and hierarchical technical disciplines by synthesizing Knowledge Graphs, FSRS scheduling, and real-time Socratic AI code evaluation. We have demonstrated a 77.5% reduction in study workload, a 97% reduction in forgetting lapses, and superior predictive calibration on official benchmarks. We express our sincere gratitude to Dr. Arti Mohanpurkar, Dr. Smita Kasar, and the examination committee. We are now open for viva voce questions.">
      <div class="slide-header">
        <div class="header-left">
          <div class="kicker">Chapter 5 · Conclusion & Defense</div>
          <div class="slide-title">Conclusion & Viva Voce Defense Readiness</div>
          <div class="slide-subtitle">Summary of primary research deliverables and technical contributions</div>
        </div>
        <div class="header-badge">Defense Conclusion</div>
      </div>
      <div class="slide-body">
        <div class="grid-2col">
          <div style="display:flex; flex-direction:column; gap:12px;">
            <div class="academic-card card-accent">
              <h3>I. Theoretical Contribution</h3>
              <p>Formulated the <b>Multi-Concept Graph Stability Propagation</b> algorithm ($\Delta S_v = \alpha w_{uv} \Delta S_u$) with 3:1 asymmetric penalty ratio to eliminate prerequisite cascading decay.</p>
            </div>
            <div class="academic-card card-accent">
              <h3>II. Pedagogical Contribution</h3>
              <p>Implemented embedded Monaco Socratic evaluation, replacing biased 4-button self-grading with objective, rubric-based continuous FSRS scores.</p>
            </div>
            <div class="academic-card card-forest">
              <h3>III. Empirical Contribution</h3>
              <p>Validated on official benchmarks and 90-day simulation: slashed study workload by <b>77.5%</b> and achieved a <b>19.4% error reduction</b> over standalone FSRS.</p>
            </div>
          </div>

          <div style="border:1.5px solid var(--border-dark); background:#faf8f5; padding:28px 24px; text-align:center; display:flex; flex-direction:column; justify-content:center; align-items:center;">
            <div style="font-family:var(--font-title); font-size:1.15rem; font-weight:700; letter-spacing:0.05em; color:var(--navy-deep); margin-bottom:6px;">
              MAHARASHTRA INSTITUTE OF TECHNOLOGY
            </div>
            <div style="font-size:0.8rem; color:var(--text-muted); font-style:italic; margin-bottom:18px;">
              Department of Computer Science and Engineering
            </div>
            
            <div style="font-family:var(--font-serif); font-size:1.6rem; font-weight:700; color:var(--navy-primary); margin-bottom:8px;">
              Thank You
            </div>
            <p style="font-size:0.86rem; color:var(--text-secondary); max-width:320px; line-height:1.5; margin-bottom:16px;">
              The floor is now open for questions, evaluation, and scholarly discussion.
            </p>
            
            <div style="display:flex; gap:8px; font-family:var(--font-mono); font-size:0.75rem;">
              <span class="header-badge">Prasad Anil Kankhar</span>
              <span class="header-badge">Prashant Anil Gande</span>
              <span class="header-badge">Aditya Devidas Kavde</span>
            </div>
          </div>
        </div>
      </div>
    </section>

  </div>
</div>

<!-- SPEAKER SCRIPT PARCHMENT DRAWER -->
<div class="speaker-drawer" id="speakerDrawer">
  <div class="speaker-drawer-header">
    <div class="speaker-title">
      <span>🎙️ DEFENSE SCRIPT & SPEAKER NOTES</span>
      <span class="speaker-tag" id="speakerTag">Prasad Anil Kankhar</span>
    </div>
    <button class="btn-academic" onclick="toggleSpeakerDrawer()" style="padding:2px 8px; font-size:0.72rem;">Close (N)</button>
  </div>
  <div class="speaker-content" id="speakerContent">
    Select a slide to view the verbatim defense script.
  </div>
</div>

<!-- BOTTOM ACADEMIC CONTROLS -->
<div class="deck-controls">
  <div style="display:flex; align-items:center; gap:12px;">
    <button class="btn-academic" onclick="prevSlide()" title="Previous Slide (Left Arrow, Page Up)">◀ Previous</button>
    <button class="btn-academic" onclick="nextSlide()" title="Next Slide (Right Arrow, Space, Page Down)">Next ▶</button>
    <div class="slide-counter">
      Slide <span id="currentSlideNum">1</span> of <span id="totalSlideNum">10</span>
    </div>
  </div>

  <div class="progress-track">
    <div class="progress-fill" id="progressFill"></div>
  </div>

  <div style="display:flex; align-items:center; gap:12px;">
    <button class="btn-academic" id="btnNotes" onclick="toggleSpeakerDrawer()" title="Toggle Speaker Script (Key: N or S)">
      📝 Spoken Script (N)
    </button>
    <button class="btn-academic" onclick="toggleFullscreen()" title="Toggle Fullscreen (Key: F)">
      ⛶ Fullscreen (F)
    </button>
  </div>
</div>

<script>
  let currentSlideIndex = 0;
  const slides = document.querySelectorAll('.slide');
  const totalSlides = slides.length;
  const currentSlideNumEl = document.getElementById('currentSlideNum');
  const totalSlideNumEl = document.getElementById('totalSlideNum');
  const progressFillEl = document.getElementById('progressFill');
  const speakerDrawer = document.getElementById('speakerDrawer');
  const speakerContent = document.getElementById('speakerContent');
  const speakerTag = document.getElementById('speakerTag');
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
    progressFillEl.style.width = progressPercent + '%';

    // Update Speaker Script
    const activeSlide = slides[currentSlideIndex];
    const notes = activeSlide.getAttribute('data-notes') || 'No notes for this slide.';
    const speaker = activeSlide.getAttribute('data-speaker') || 'Presenter';
    speakerContent.innerHTML = notes;
    speakerTag.textContent = 'Speaker: ' + speaker;
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
    btnNotes.classList.toggle('active-btn');
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
    f.write(academic_html)

print("Generated Academic-Themed presentation/index.html successfully!")
