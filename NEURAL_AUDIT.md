# Project Neural Audit Report
Date: 2026-05-23

## 1. Project Component Map (What we have)

### Frontend (React SPA)
- **Knowledge Graph (Neural Plane):** Advanced 2D force-directed graph visualization of concepts and their relationships. Supports subject-based highlighting and synaptic detail inspection.
- **AI Tutor:** Integrated Socratic tutoring system with persona support (bio). Features include bridge suggestion, concept connection, and automated flashcard generation.
- **Study Engine:** Active recall interface with AI-powered grading. Supports multi-concept FSRS scheduling and latency tracking.
- **Analytics Dashboard:** Comprehensive telemetry suite covering retention curves, stability distribution, algorithm comparison (SM2 vs FSRS), and neural activity heatmaps.
- **Code Editor:** IDE-like environment with support for JavaScript, Python, C++, and HTML. Features local JS execution and console mirroring.
- **Subject Management:** CRUD interface for organizing concepts into hierarchical clusters.

### Backend (FastAPI + SQLAlchemy)
- **Neural Algorithms:**
  - `multi_fsrs.py`: Extension of Free Spaced Repetition Scheduler for interconnected concepts.
  - `propagation.py`: Logic for memory stability decay across synaptic links.
  - `knowledge_graph.py`: Central logic for graph state and weighting.
- **AI Integration:**
  - `ai.py` router: Interfaces with Groq (Llama 3) for Socratic evaluation and content generation.
- **Data Layer:**
  - SQLite database with Alembic migrations.
  - Models for Users, Subjects, Concepts, Review Logs, and Propagation Logs.

---

## 2. API Inventory & Usage Audit

### Used Endpoints (Active)
- `GET /auth/me`: User session validation.
- `POST /auth/login`: Authentication.
- `POST /auth/register`: User onboarding.
- `GET /ai/advisor`: Socratic study advice.
- `POST /ai/generate-flashcards`: Automated content creation.
- `POST /ai/save-flashcards`: Persistence of AI-generated cards.
- `POST /ai/evaluate-answer`: Neural grading of student responses.
- `POST /ai/connect-concepts`: Semantic discovery of new synapses.
- `GET /analytics/*`: (Overview, Compare, Retention, Stability, etc.) - All active in Analytics page.
- `GET /graph/full`: Core data provider for the Neural Plane.
- `GET /reviews/due`: Daily study queue.
- `POST /reviews/submit`: Logging active recall performance.
- `GET /subjects/`: Subject listing and management.
- `GET /concepts/`: Concept retrieval (filtered by subject).
- `GET /schedule/{id}`: Real-time FSRS metrics for individual concepts.

### Unused Endpoints (Dead/Stale)
- `POST /ai/suggest-bridges`: Backend logic exists but UI does not call it.
- `POST /analytics/optimize-fsrs`: Backend optimization logic present but not exposed to users.
- `POST /graph/tune-weights`: Weights can be tuned in DB but not via UI.
- `GET /graph/logs/{id}`: Propagation logs are recorded but not visualized in the frontend.
- `POST /concepts/{id}/questions`: QuizQuestion system is partially implemented but unused in the current "Study" flow.

---

## 3. Unused Code & Stale Resources
- **Models:** `PerformanceLog` model exists in `models/performance_log.py` but is not utilized by the main application logic.
- **Scripts:** Several scripts in `backend/scripts/` (e.g., `backfill_semantic_weights.py`) are one-time utilities not needed for runtime.
- **Images:** `frontend/src/assets/react.svg` and `vite.svg` are default boilerplate assets not used in the custom UI.

---

## 4. Improvements & Future Roadmap

### Technical Improvements
- **Code Execution:** Move Code Editor execution to the backend using a sandboxed environment (Docker/Pyodide) for non-JS languages.
- **Graph Optimization:** Implement WebWorker for force-graph calculations to improve performance on low-end devices for large graphs (1000+ nodes).
- **Persistent Memory:** Migrate from SQLite to PostgreSQL for better concurrency handling during heavy AI evaluation tasks.

### Missing Features (Additions)
- **Neural Search:** Add a global command palette (Ctrl+K) to instantly search and jump to concepts in the Neural Plane.
- **Algorithm Tuner:** Expose the `optimize-fsrs` and `tune-weights` endpoints in a "Settings" page to allow users to customize their learning physics.
- **Synaptic Replay:** A feature to visualize the "Propagation" of memory through links over time (utilizing the currently unused `PropagationLog` data).
- **Dark Mode Standard:** While the UI is dark, implementing a true CSS-variable based theme system would allow for easier accessibility adjustments.
