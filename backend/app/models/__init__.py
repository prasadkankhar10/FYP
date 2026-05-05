"""
models/__init__.py — Import all models so Alembic can detect them.
Order matters: Base must be imported before any model that follows.
"""
from app.database import Base  # noqa: F401
from app.models.user import User  # noqa: F401
from app.models.subject import Subject  # noqa: F401
from app.models.concept import Concept  # noqa: F401
from app.models.scheduling import SchedulingData  # noqa: F401
from app.models.review_log import ReviewLog  # noqa: F401
from app.models.performance_log import PerformanceLog  # noqa: F401
from app.models.quiz_question import QuizQuestion  # noqa: F401
from app.models.concept_edge import ConceptEdge  # noqa: F401
from app.models.propagation_log import PropagationLog  # noqa: F401
