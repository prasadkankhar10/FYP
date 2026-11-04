# Project Roadmap

## Phase 1: Engineering & Validation (Foundation)
**Goal:** Establish a robust safety net to prevent regressions during complex algorithm and AI feature development.
- Write unit tests for FastAPI routers (`ai.py`, `reviews.py`, `scheduling.py`).
- Write unit tests for the AI integration service.
- *Verification:* `pytest` passes with high coverage.

## Phase 2: AI Tutor Deepening
**Goal:** Enhance the AI Tutor to be more interactive and effective at knowledge distillation.
- Update `evaluate-answer` to support "Socratic Tutor" mode (generating follow-up questions).
- Enhance `generate-flashcards` logic for better atomic breakdown and graph linking.
- *Verification:* The AI endpoints successfully return structured Socratic feedback and well-formatted flashcards.

## Phase 3: Algorithm Enhancements
**Goal:** Make the scheduling algorithm dynamic and personalized.
- Implement logic to optimize `fsrs_params` in the `User` model based on review history.
- Implement dynamic tuning of `alpha`, `beta`, `gamma` coefficients.
- Extend semantic graph building to suggest new bridging concepts.
- *Verification:* Users receive custom FSRS parameters after sufficient reviews; semantic bridges are generated.

## Phase 4: UX & Analytics
**Goal:** Polish the frontend for a production-level experience.
- Build time-series "Forgetting Curves" and "Knowledge Heatmaps" in the Analytics Dashboard.
- Improve Knowledge Graph performance scaling for large node counts.
- Add an onboarding tour and Import/Export functionality.
- *Verification:* UI renders smoothly with 500+ nodes; new charts display correctly.
