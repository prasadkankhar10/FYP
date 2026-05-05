"""
routers/ai.py — Groq Llama3 integrated endpoints.
Handles Academic Advisor, Auto-Flashcards, and Concept Connector logic.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database import get_db
from app.models.user import User
from app.models.subject import Subject
from app.models.concept import Concept
from app.models.scheduling import SchedulingData
from app.schemas.ai import AIAdviceResponse, AutoFlashcardRequest, AutoFlashcardResponse, ConnectConceptsResponse
from app.algorithms.knowledge_graph import GraphManager
from app.utils.auth import get_current_user
from app.config import settings
import app.schemas.ai
import json
import os
import random

try:
    from groq import Groq
except ImportError:
    Groq = None

router = APIRouter()

def get_groq_client():
    if not Groq:
        raise HTTPException(status_code=500, detail="Groq library not installed.")
    
    api_key = settings.GROQ_API_KEY
    if not api_key:
        # Fallback to os.environ if settings didn't catch it properly
        api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured.")
    return Groq(api_key=api_key)


@router.get("/advisor", response_model=AIAdviceResponse)
def get_advisor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Acts as a personalized academic advisor.
    Feeds the user's bio and current subjects into Llama 3 via Groq for highly tailored advice.
    """
    client = get_groq_client()

    subjects = db.query(Subject).filter(Subject.user_id == current_user.id).all()
    subject_names = [s.name for s in subjects]
    
    bio = current_user.bio if current_user.bio else "I am an enthusiastic learner exploring new topics."
    
    system_prompt = (
        "You are an elite academic advisor. You are precise, highly sophisticated, and insightful. "
        "Your goal is to guide the user towards academic excellence. Do not use generic filler words."
    )
    
    user_prompt = f"""
    Here is a profile of the student:
    {bio}

    Currently, they are studying the following subjects:
    {', '.join(subject_names) if subject_names else 'No active subjects yet.'}

    Based strictly on their profile goals and what they are currently studying, provide:
    1. A short, highly motivating analysis of their current trajectory.
    2. Exactly 3 new interconnected 'Subjects' they should add to their deck right now to progress.
    3. For each of the 3 subjects, recommend 2 specific key 'Concepts' (Flashcards) they should create.
    Format your response beautifully in Markdown.
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        return AIAdviceResponse(advice_markdown=completion.choices[0].message.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-flashcards", response_model=AutoFlashcardResponse)
def generate_flashcards(
    payload: AutoFlashcardRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Automagically converts a block of text into atomic Question/Answer flashcards 
    and saves them directly to the database.
    """
    client = get_groq_client()
    
    subject = db.query(Subject).filter(Subject.id == payload.subject_id, Subject.user_id == current_user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    system_prompt = (
        "You are an expert curriculum designer. Extract core, atomic knowledge from the provided text "
        "and format it EXACTLY as a raw JSON array of objects. Do not write any other markdown or text. "
        "Format: [{\"title\": \"Question/Concept Name\", \"content\": \"Detailed Answer/Explanation\"}]"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract 3 to 5 vital flashcards from this text:\n\n{payload.source_text}"}
            ],
            temperature=0.3,
            max_tokens=1024,
        )
        
        # Parse the JSON response
        response_text = completion.choices[0].message.content.strip()
        if response_text.startswith("```json"): response_text = response_text[7:]
        if response_text.startswith("```"): response_text = response_text[3:]
        if response_text.endswith("```"): response_text = response_text[:-3]
            
        flashcards = json.loads(response_text)
        
        cards_out = []
        for card in flashcards:
            cards_out.append({
                "title": card.get("title", "Untitled"),
                "content": card.get("content", "")
            })
            
        return AutoFlashcardResponse(message="Flashcards generated successfully for preview.", cards=cards_out)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate flashcards: {str(e)}")


@router.post("/save-flashcards", response_model=app.schemas.ai.SaveFlashcardsResponse)
def save_flashcards(
    payload: app.schemas.ai.SaveFlashcardsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Saves the approved flashcards to the database."""
    subject = db.query(Subject).filter(Subject.id == payload.subject_id, Subject.user_id == current_user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    count = 0
    try:
        for card in payload.cards:
            new_concept = Concept(
                user_id=current_user.id,
                subject_id=subject.id,
                title=card.title,
                content=card.content,
            )
            db.add(new_concept)
            db.flush()
            
            # Auto-assign scheduling baseline randomly to fuel A/B/C testing
            sched = SchedulingData(
                user_id=current_user.id, 
                concept_id=new_concept.id,
                algorithm=random.choice(["sm2", "fsrs", "multi_fsrs"]),
                next_review_date=datetime.now(timezone.utc),
            )
            db.add(sched)
            count += 1
            
        db.commit()
        return app.schemas.ai.SaveFlashcardsResponse(message="Successfully saved flashcards.", concepts_created=count)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save flashcards: {str(e)}")


@router.post("/connect-concepts", response_model=ConnectConceptsResponse)
def connect_concepts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyzes the user's concepts and uses AI to automatically detect prerequisite relationships 
    to supercharge the Multi-Concept FSRS algorithm!
    """
    client = get_groq_client()
    
    concepts = db.query(Concept).filter(Concept.user_id == current_user.id, Concept.parent_concept_id == None).all()
    if len(concepts) < 2:
        return ConnectConceptsResponse(message="Not enough unconnected concepts to analyze.", connections_made=0)

    # For large datasets, we'd need embeddings. For FYP, we send a limited list.
    concept_list = [{"id": c.id, "title": c.title} for c in concepts[:50]]
    
    system_prompt = (
        "You are an AI logic mapper. Analyze the provided list of academic concepts. "
        "Identify logical prerequisite relationships. (E.g. 'Addition' is a prerequisite to 'Multiplication'). "
        "Return EXACTLY a raw JSON array of paired IDs. Do not write any other markdown. "
        "Format: [{\"child_id\": 10, \"parent_id\": 5}]"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(concept_list)}
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        
        response_text = completion.choices[0].message.content.strip()
        if response_text.startswith("```json"): response_text = response_text[7:]
        if response_text.startswith("```"): response_text = response_text[3:]
        if response_text.endswith("```"): response_text = response_text[:-3]

        pairs = json.loads(response_text)
        
        connections = 0
        for pair in pairs:
            child_id = pair.get("child_id")
            parent_id = pair.get("parent_id")
            if child_id and parent_id and child_id != parent_id:
                child_concept = db.query(Concept).filter(Concept.id == child_id, Concept.user_id == current_user.id).first()
                parent_concept = db.query(Concept).filter(Concept.id == parent_id, Concept.user_id == current_user.id).first()
                if child_concept and parent_concept:
                    child_concept.parent_concept_id = parent_id
                    # Also create a graph edge so Multi-FSRS can see the relationship
                    try:
                        GraphManager.add_edge(
                            db=db,
                            user_id=current_user.id,
                            source_id=parent_id,
                            target_id=child_id,
                            w_expert=0.5,
                        )
                    except ValueError:
                        pass  # Edge already exists or limit reached — not critical
                    connections += 1
                    
        db.commit()
        return ConnectConceptsResponse(message="Graph optimized.", connections_made=connections)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to connect concepts: {str(e)}")


@router.post("/evaluate-answer", response_model=app.schemas.ai.AIEvaluateResponse)
def evaluate_answer(
    payload: app.schemas.ai.AIEvaluateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Grades user's free-text active recall response against the true answer mathematically,
    returning an SM-2 rating, an FSRS rating, and personalized feedback.
    """
    client = get_groq_client()
    
    concept = db.query(Concept).filter(Concept.id == payload.concept_id, Concept.user_id == current_user.id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    system_prompt = (
        "You are an elite, strict academic evaluator. Your job is to compare a student's answer "
        "from memory against the True System Answer. "
        "Evaluate their response strictly for factual correctness, missing nuance, and overall grasp of the material.\n\n"
        "Return EXACTLY a raw JSON object formatting using this schema:\n"
        "{\n"
        "  \"sm2_score\": <integer 0 to 5>,\n"
        "  \"fsrs_score\": <integer 1 to 4>,\n"
        "  \"feedback_markdown\": \"<your detailed, encouraging but strict critique of what they missed or got right formatted as markdown>\",\n"
        "  \"confidence_score\": <float 0.0 to 1.0 indicating how confident you are in this grade based on the ambiguity of the student's answer>\n"
        "}\n\n"
        "GRADING SCALES:\n"
        "SM-2 (0-5):\n"
        "0 = Blackout completely wrong\n"
        "1 = Incorrect but recognized\n"
        "2 = Incorrect but familiar\n"
        "3 = Passed but difficult (barely right)\n"
        "4 = Good pass with minor errors\n"
        "5 = Perfect recall\n\n"
        "FSRS (1-4):\n"
        "1 = Again (failed entirely or missed core concept)\n"
        "2 = Hard (passed but struggled greatly, messy)\n"
        "3 = Good (passed standard)\n"
        "4 = Easy (flawless)\n"
        "IMPORTANT: Do not wrap your response in markdown code blocks. Output RAW JSON."
    )

    user_prompt = f"""
    Flashcard Question / Topic:
    {concept.title}

    True System Answer:
    {concept.content}

    Student's Typed Answer:
    {payload.typed_answer}
    """

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=1024,
        )
        
        response_text = completion.choices[0].message.content.strip()
        if response_text.startswith("```json"): response_text = response_text[7:]
        if response_text.startswith("```"): response_text = response_text[3:]
        if response_text.endswith("```"): response_text = response_text[:-3]

        evaluation = json.loads(response_text)
        
        return app.schemas.ai.AIEvaluateResponse(
            sm2_score=evaluation.get("sm2_score", 1),
            fsrs_score=evaluation.get("fsrs_score", 1),
            feedback_markdown=evaluation.get("feedback_markdown", "Failed to parse feedback."),
            confidence_score=evaluation.get("confidence_score", 0.9)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate answer: {str(e)}")
