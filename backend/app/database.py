"""
database.py — SQLAlchemy engine + session factory.
All models import Base from here and all routers get db via get_db().

Uses SQLite by default (zero-install, file-based).
The database file is stored at backend/arsps.db.
"""
import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Detect if we're using SQLite (need special handling)
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

# Engine kwargs differ between SQLite and PostgreSQL
engine_kwargs = {}
if is_sqlite:
    # SQLite requires check_same_thread=False for FastAPI's threaded access
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL connection pool settings
    engine_kwargs["pool_pre_ping"] = True
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

# Create the database engine
engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# Enable SQLite WAL mode and foreign keys (only for SQLite)
if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")       # Better concurrent read performance
        cursor.execute("PRAGMA foreign_keys=ON")         # Enforce FK constraints
        cursor.execute("PRAGMA busy_timeout=5000")       # Wait 5s on lock instead of failing
        cursor.close()

# Session factory — used in routers via Depends(get_db)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All ORM models inherit from this Base
Base = declarative_base()


def init_db():
    """
    Create all tables if they don't exist.
    Called on application startup so team members never need to run
    manual migration commands — tables are auto-created.
    """
    import app.models  # noqa: F401 — registers all models with Base
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
