"""
models/quiz_question.py — QuizQuestion ORM model.
Each Concept can have multiple quiz questions.
Supports MCQ, recall (free text), and true/false types.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    concept_id = Column(Integer, ForeignKey("concepts.id"), nullable=False)

    question_text = Column(Text, nullable=False)

    # Question type: mcq | recall | truefalse
    question_type = Column(String(20), default="mcq")

    # JSON string: ["Option A", "Option B", "Option C", "Option D"]
    # Null for recall-type questions
    options = Column(Text, nullable=True)

    correct_answer = Column(Text, nullable=False)

    # Difficulty: 1 (easy) to 5 (very hard)
    difficulty_level = Column(Integer, default=3)

    # Relationships
    concept = relationship("Concept", back_populates="quiz_questions")
