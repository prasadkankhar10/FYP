import pytest
from unittest.mock import MagicMock, patch
from app.models.subject import Subject
from app.models.concept import Concept
from app.models.review_log import ReviewLog
from datetime import datetime, timezone
import json

def test_optimize_fsrs(client, auth_headers, test_user, db):
    # Add 50 reviews to bypass the limit
    subject = Subject(name="Math", user_id=test_user.id)
    db.add(subject)
    db.commit()
    
    concept = Concept(title="Algebra", content="...", user_id=test_user.id, subject_id=subject.id)
    db.add(concept)
    db.commit()
    
    for i in range(50):
        log = ReviewLog(
            user_id=test_user.id,
            concept_id=concept.id,
            quality_score=3,
            was_correct=True,
            algorithm_used="fsrs",
            reviewed_at=datetime.now(timezone.utc)
        )
        db.add(log)
    db.commit()

    response = client.post("/analytics/optimize-fsrs", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "params" in response.json()
    
    # Check if user model updated
    db.refresh(test_user)
    assert test_user.fsrs_params is not None

def test_tune_weights(client, auth_headers, test_user, db):
    # Add some reviews
    subject = Subject(name="Math", user_id=test_user.id)
    db.add(subject)
    db.commit()
    
    concept = Concept(title="Algebra", content="...", user_id=test_user.id, subject_id=subject.id)
    db.add(concept)
    db.commit()
    
    for i in range(150): # Enough to trigger heuristic change
        log = ReviewLog(
            user_id=test_user.id,
            concept_id=concept.id,
            quality_score=3,
            was_correct=True,
            algorithm_used="multi_fsrs",
            reviewed_at=datetime.now(timezone.utc)
        )
        db.add(log)
    db.commit()

    response = client.post("/graph/tune-weights", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    
    params = response.json()["params"]
    # With 150 reviews, beta_shift = (150 // 100) * 0.05 = 0.05
    # new_alpha = 0.5 - 0.05 = 0.45
    # new_beta = 0.3 + 0.05 = 0.35
    assert params["alpha"] == 0.45
    assert params["beta"] == 0.35
    
    db.refresh(test_user)
    assert test_user.kg_params is not None

@patch("app.routers.ai.get_groq_client")
def test_suggest_bridges(mock_get_groq, client, auth_headers, test_user, db):
    # Mock Groq response
    mock_client = MagicMock()
    mock_get_groq.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = (
        '[{"title": "Bridge Concept", "content": "Links A and B", "rationale": "Logical connection"}]'
    )

    # Add concepts
    subject = Subject(name="Science", user_id=test_user.id)
    db.add(subject)
    db.commit()
    
    c1 = Concept(title="Physics", content="...", user_id=test_user.id, subject_id=subject.id)
    c2 = Concept(title="Math", content="...", user_id=test_user.id, subject_id=subject.id)
    db.add_all([c1, c2])
    db.commit()

    response = client.post("/ai/suggest-bridges", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()["suggestions"]) == 1
    assert response.json()["suggestions"][0]["title"] == "Bridge Concept"
