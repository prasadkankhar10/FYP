import pytest
from unittest.mock import MagicMock, patch
from app.models.subject import Subject
from app.models.concept import Concept
from app.models.scheduling import SchedulingData

@patch("app.routers.ai.get_groq_client")
def test_get_advisor(mock_get_groq, client, auth_headers, test_user, db):
    # Mock Groq response
    mock_client = MagicMock()
    mock_get_groq.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = "Expert Advice"

    # Add a subject for the user
    subject = Subject(name="Biology", user_id=test_user.id)
    db.add(subject)
    db.commit()

    response = client.get("/ai/advisor", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["advice_markdown"] == "Expert Advice"
    mock_client.chat.completions.create.assert_called_once()

@patch("app.routers.ai.get_groq_client")
def test_generate_flashcards(mock_get_groq, client, auth_headers, test_user, db):
    # Mock Groq response with relationship
    mock_client = MagicMock()
    mock_get_groq.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = (
        '[{"title": "Cell", "content": "Basic unit of life", "parent_concept": null}, '
        ' {"title": "Mitosis", "content": "Cell division", "parent_concept": "Cell"}]'
    )

    # Add a subject
    subject = Subject(name="Biology", user_id=test_user.id)
    db.add(subject)
    db.commit()

    payload = {"subject_id": subject.id, "source_text": "Cells and mitosis"}
    response = client.post("/ai/generate-flashcards", json=payload, headers=auth_headers)
    
    assert response.status_code == 200
    assert len(response.json()["cards"]) == 2
    assert response.json()["cards"][0]["title"] == "Cell"
    assert response.json()["cards"][1]["parent_concept"] == "Cell"

def test_save_flashcards(client, auth_headers, test_user, db):
    # Add a subject
    subject = Subject(name="Biology", user_id=test_user.id)
    db.add(subject)
    db.commit()

    payload = {
        "subject_id": subject.id,
        "cards": [
            {"title": "Cell", "content": "Basic unit of life", "parent_concept": None},
            {"title": "Mitosis", "content": "Cell division", "parent_concept": "Cell"}
        ]
    }
    response = client.post("/ai/save-flashcards", json=payload, headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["concepts_created"] == 2
    
    # Check DB
    cell = db.query(Concept).filter(Concept.title == "Cell", Concept.subject_id == subject.id).first()
    mitosis = db.query(Concept).filter(Concept.title == "Mitosis", Concept.subject_id == subject.id).first()
    
    assert cell is not None
    assert mitosis is not None
    assert mitosis.parent_concept_id == cell.id
    
    # Check scheduling data was created
    scheds = db.query(SchedulingData).filter(SchedulingData.user_id == test_user.id).all()
    assert len(scheds) == 2

@patch("app.routers.ai.get_groq_client")
def test_connect_concepts(mock_get_groq, client, auth_headers, test_user, db):
    # Mock Groq response
    mock_client = MagicMock()
    mock_get_groq.return_value = mock_client
    
    # Add a subject
    subject = Subject(name="Biology", user_id=test_user.id)
    db.add(subject)
    db.commit()

    # Add two concepts
    c1 = Concept(title="Cell", content="...", user_id=test_user.id, subject_id=subject.id)
    c2 = Concept(title="Mitosis", content="...", user_id=test_user.id, subject_id=subject.id)
    db.add_all([c1, c2])
    db.commit()

    mock_client.chat.completions.create.return_value.choices[0].message.content = f'[{{"child_id": {c2.id}, "parent_id": {c1.id}}}]'

    response = client.post("/ai/connect-concepts", headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["connections_made"] == 1
    
    db.refresh(c2)
    assert c2.parent_concept_id == c1.id

@patch("app.routers.ai.get_groq_client")
def test_evaluate_answer(mock_get_groq, client, auth_headers, test_user, db):
    # Mock Groq response with follow-up
    mock_client = MagicMock()
    mock_get_groq.return_value = mock_client
    mock_client.chat.completions.create.return_value.choices[0].message.content = (
        '{"sm2_score": 3, "fsrs_score": 2, "feedback_markdown": "Close, but you missed X.", '
        ' "confidence_score": 0.9, "follow_up_question": "What is the role of X in this process?"}'
    )

    # Add a subject
    subject = Subject(name="Biology", user_id=test_user.id)
    db.add(subject)
    db.commit()

    # Add a concept
    concept = Concept(title="Photosynthesis", content="Sunlight to energy", user_id=test_user.id, subject_id=subject.id)
    db.add(concept)
    db.commit()

    payload = {"concept_id": concept.id, "typed_answer": "Plants use sunlight"}
    response = client.post("/ai/evaluate-answer", json=payload, headers=auth_headers)
    
    assert response.status_code == 200
    assert response.json()["sm2_score"] == 3
    assert response.json()["follow_up_question"] == "What is the role of X in this process?"
