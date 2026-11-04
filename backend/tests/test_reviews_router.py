import pytest
from datetime import datetime, timedelta, timezone
from app.models.subject import Subject
from app.models.concept import Concept
from app.models.scheduling import SchedulingData
from app.models.review_log import ReviewLog

def test_get_due_reviews_empty(client, auth_headers):
    response = client.get("/reviews/due", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []

def test_get_due_reviews(client, auth_headers, test_user, db):
    # Add subject, concept, and scheduling data
    subject = Subject(name="Math", user_id=test_user.id)
    db.add(subject)
    db.commit()

    concept = Concept(title="Addition", content="1+1=2", subject_id=subject.id, user_id=test_user.id)
    db.add(concept)
    db.commit()

    # Create due scheduling data
    now = datetime.now(timezone.utc)
    sched = SchedulingData(
        concept_id=concept.id,
        user_id=test_user.id,
        algorithm="sm2",
        next_review_date=now - timedelta(days=1),
        retrievability=0.5
    )
    db.add(sched)
    db.commit()

    response = client.get("/reviews/due", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["concept_id"] == concept.id
    assert data[0]["concept_title"] == "Addition"

def test_submit_review_sm2(client, auth_headers, test_user, db):
    subject = Subject(name="Math", user_id=test_user.id)
    db.add(subject)
    db.commit()
    concept = Concept(title="Addition", content="1+1=2", subject_id=subject.id, user_id=test_user.id)
    db.add(concept)
    db.commit()
    sched = SchedulingData(
        concept_id=concept.id,
        user_id=test_user.id,
        algorithm="sm2",
        next_review_date=datetime.now(timezone.utc)
    )
    db.add(sched)
    db.commit()

    payload = {
        "concept_id": concept.id,
        "quality_score": 4,
        "was_correct": True,
        "response_time_sec": 5.0
    }
    response = client.post("/reviews/submit", json=payload, headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["quality_score"] == 4
    
    # Check if log was created
    logs = db.query(ReviewLog).filter(ReviewLog.concept_id == concept.id).all()
    assert len(logs) == 1

def test_submit_review_invalid_score(client, auth_headers, test_user, db):
    subject = Subject(name="Math", user_id=test_user.id)
    db.add(subject)
    db.commit()
    concept = Concept(title="Addition", content="1+1=2", subject_id=subject.id, user_id=test_user.id)
    db.add(concept)
    db.commit()
    sched = SchedulingData(
        concept_id=concept.id,
        user_id=test_user.id,
        algorithm="sm2",
        next_review_date=datetime.now(timezone.utc)
    )
    db.add(sched)
    db.commit()

    # SM-2 quality score must be 0-5
    payload = {
        "concept_id": concept.id,
        "quality_score": 6,
        "was_correct": True
    }
    response = client.post("/reviews/submit", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "SM-2 quality score must be 0–5" in response.json()["detail"]

def test_get_history(client, auth_headers, test_user, db):
    subject = Subject(name="Math", user_id=test_user.id)
    db.add(subject)
    db.commit()
    concept = Concept(title="Addition", content="1+1=2", subject_id=subject.id, user_id=test_user.id)
    db.add(concept)
    db.commit()
    
    log = ReviewLog(
        concept_id=concept.id,
        user_id=test_user.id,
        algorithm_used="sm2",
        quality_score=5,
        was_correct=True,
        reviewed_at=datetime.now(timezone.utc)
    )
    db.add(log)
    db.commit()

    response = client.get("/reviews/history", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["quality_score"] == 5
