"""
# Forced reload for bcrypt downgrade
main.py — FastAPI application entry point.
Registers all routers and configures CORS for frontend dev server.
Uses SQLite — no Docker or external database required.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import auth, subjects, concepts, reviews, scheduling, analytics, ai, graph

app = FastAPI(
    title="Adaptive Review Scheduling System",
    description="FYP — SM-2, FSRS, Multi-Concept FSRS scheduling engine",
    version="1.0.0",
)

# ── CORS — allow React dev server (port 5173) ─────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ──────────────────────────────────────────────────────────
app.include_router(auth.router,       prefix="/auth",       tags=["Authentication"])
app.include_router(subjects.router,   prefix="/subjects",   tags=["Subjects"])
app.include_router(concepts.router,   prefix="/concepts",   tags=["Concepts"])
app.include_router(reviews.router,    prefix="/reviews",    tags=["Reviews"])
app.include_router(scheduling.router, prefix="/schedule",   tags=["Scheduling"])
app.include_router(analytics.router,  prefix="/analytics",  tags=["Analytics"])
app.include_router(ai.router,         prefix="/ai",         tags=["AI"])
app.include_router(graph.router,      prefix="/graph",      tags=["Knowledge Graph"])

# ── Auto-create database tables on startup ────────────────────────────────────
# This ensures any team member can just run the server — no Docker, no manual
# migration commands. SQLite DB + all tables are created automatically.
@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "ARSPS API is running"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
