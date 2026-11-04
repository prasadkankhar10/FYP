import pytest
from datetime import datetime, timezone
from app.models.subject import Subject
from app.models.concept import Concept
from app.models.scheduling import SchedulingData

def test_get_today_queue(client, auth_headers, test_user, db):
    # Add subject, concept, and scheduling data
    subject = Subject(name="Physics", user_id=test_user.id)
    db.add(subject)
    db.commit()

    concept = Concept(title="Gravity", content="F=mg", subject_id=subject.id, user_id=test_user.id)
    db.add(concept)
    db.commit()

    sched = SchedulingData(
        concept_id=concept.id,
        user_id=test_user.id,
        algorithm="fsrs",
        next_review_date=datetime.now(timezone.utc),
        retrievability=0.9
    )
    db.add(sched)
    db.commit()

    response = client.get("/schedule/today", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["concept_title"] == "Gravity"

def test_switch_algorithm(client, auth_headers, test_user, db):
    subject = Subject(name="Physics", user_id=test_user.id)
    db.add(subject)
    db.commit()
    concept = Concept(title="Gravity", content="F=mg", subject_id=subject.id, user_id=test_user.id)
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

    payload = {"algorithm": "fsrs"}
    response = client.post(f"/schedule/algorithm/{concept.id}", json=payload, headers=auth_headers)
    
    assert response.status_code == 200
    assert "Algorithm switched to fsrs" in response.json()["message"]
    
    db.refresh(sched)
    assert sched.algorithm == "fsrs"

def test_switch_algorithm_invalid(client, auth_headers, test_user, db):
    subject = Subject(name="Physics", user_id=test_user.id)
    db.add(subject)
    db.commit()
    concept = Concept(title="Gravity", content="F=mg", subject_id=subject.id, user_id=test_user.id)
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

    payload = {"algorithm": "invalid_algo"}
    response = client.post(f"/schedule/algorithm/{concept.id}", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "Algorithm must be one of" in response.json()["detail"]

def test_get_scheduling_data(client, auth_headers, test_user, db):
    subject = Subject(name="Physics", user_id=test_user.id)
    db.add(subject)
    db.commit()
    concept = Concept(title="Gravity", content="F=mg", subject_id=subject.id, user_id=test_user.id)
    db.add(concept)
    db.commit()
    sched = SchedulingData(
        concept_id=concept.id,
        user_id=test_user.id,
        algorithm="sm2",
        next_review_date=datetime.now(timezone.utc),
        stability=10.5
    )
    db.add(sched)
    db.commit()

    response = client.get(f"/schedule/{concept.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["stability"] == 10.5
    assert response.json()["algorithm"] == "sm2"
