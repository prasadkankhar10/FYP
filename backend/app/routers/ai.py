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
from app.schemas.ai import AIAdviceResponse, AutoFlashcardRequest, AutoFlashcardResponse, ConnectConceptsResponse, SuggestBridgesResponse, BridgeSuggestion, ExamRecapResponse
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


def call_ai_completion(system_prompt: str, user_prompt: str, is_json: bool = False, temperature: float = 0.7) -> str:
    import requests
    import os
    from app.config import settings

    # Try Gemini first
    gemini_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            payload = {
                "systemInstruction": {
                    "parts": [{"text": system_prompt}]
                },
                "contents": [{
                    "parts": [{"text": user_prompt}]
                }],
                "generationConfig": {
                    "temperature": temperature
                }
            }
            if is_json:
                payload["generationConfig"]["responseMimeType"] = "application/json"

            headers = {"Content-Type": "application/json"}
            res = requests.post(url, json=payload, headers=headers, timeout=15)
            if res.status_code == 200:
                data = res.json()
                parts = data["candidates"][0]["content"]["parts"]
                text_response = parts[0]["text"]
                return text_response
            else:
                print(f"Gemini API returned status code {res.status_code}: {res.text}. Falling back to Groq.")
        except Exception as e:
            print(f"Failed to call Gemini API: {e}. Falling back to Groq.")

    # Fallback to Groq
    client = get_groq_client()
    completion = client.chat.completions.create(
        model="qwen/qwen3.6-27b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=4096,
    )
    return completion.choices[0].message.content


@router.get("/advisor", response_model=AIAdviceResponse)
def get_advisor(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Acts as a personalized academic advisor.
    Feeds the user's bio and current subjects into Llama 3 via Groq for highly tailored advice.
    """

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
        content = call_ai_completion(system_prompt, user_prompt, temperature=0.7)
        return AIAdviceResponse(advice_markdown=content)
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
    subject = db.query(Subject).filter(Subject.id == payload.subject_id, Subject.user_id == current_user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    system_prompt = (
        "You are an expert curriculum designer. Extract core, ATOMIC knowledge from the provided text. "
        "Each flashcard must cover exactly ONE concept. Avoid complex lists or multi-part answers.\n\n"
        "RELATIONSHIPS: Identify if any generated flashcard is a prerequisite or a parent to another card in THIS set. "
        "Use the 'parent_concept' field to store the EXACT 'title' of the parent card.\n\n"
        "Format EXACTLY as a raw JSON array of objects. Do not write any other markdown or text. "
        "Format: [{\"title\": \"Concept Name\", \"content\": \"Detailed Atomic Answer\", \"parent_concept\": \"Title of Parent Card or null\"}]"
    )

    try:
        response_text = call_ai_completion(
            system_prompt, 
            f"Extract 3 to 5 atomic flashcards from this text and suggest parent-child links where logical:\n\n{payload.source_text}",
            is_json=True,
            temperature=0.3
        )
        
        # Parse the JSON response
        import re, ast
        response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
        match = re.search(r'\[[\s\S]*\]', response_text)
        if match:
            response_text = match.group(0)
        else:
            response_text = "[]"
        try:
            flashcards = json.loads(response_text)
        except Exception:
            try:
                flashcards = ast.literal_eval(response_text)
            except Exception:
                flashcards = []
        
        cards_out = []
        for card in flashcards:
            cards_out.append({
                "title": card.get("title", "Untitled"),
                "content": card.get("content", ""),
                "parent_concept": card.get("parent_concept")
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
    created_concepts = {}  # title -> concept object
    try:
        # First pass: Create concepts and scheduling data
        for card in payload.cards:
            new_concept = Concept(
                user_id=current_user.id,
                subject_id=subject.id,
                title=card.title,
                content=card.content,
            )
            db.add(new_concept)
            db.flush()
            created_concepts[card.title] = new_concept
            
            # Auto-assign scheduling baseline randomly to fuel A/B/C testing
            sched = SchedulingData(
                user_id=current_user.id, 
                concept_id=new_concept.id,
                algorithm=random.choice(["sm2", "fsrs", "multi_fsrs"]),
                next_review_date=datetime.now(timezone.utc),
            )
            db.add(sched)
            count += 1

        # Second pass: Resolve parent-child relationships from the AI's suggestions
        for card in payload.cards:
            if card.parent_concept and card.parent_concept in created_concepts:
                child_concept = created_concepts[card.title]
                parent_concept = created_concepts[card.parent_concept]
                
                child_concept.parent_concept_id = parent_concept.id
                
                # Also create a graph edge so Multi-FSRS can see the relationship immediately
                try:
                    GraphManager.add_edge(
                        db=db,
                        user_id=current_user.id,
                        source_id=parent_concept.id,
                        target_id=child_concept.id,
                        w_expert=0.5,
                    )
                except Exception:
                    pass # Ignore duplicate edges or graph errors during bulk save
            
        db.commit()
        return app.schemas.ai.SaveFlashcardsResponse(message="Successfully saved flashcards with relationships.", concepts_created=count)
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
    concepts = db.query(Concept).filter(Concept.user_id == current_user.id, Concept.parent_concept_id == None).all()
    if len(concepts) < 2:
        return ConnectConceptsResponse(message="Not enough unconnected concepts to analyze.", connections_made=0)

    # For large datasets, we'd need embeddings. For FYP, we send a limited list.
    import random
    sampled_concepts = random.sample(concepts, min(len(concepts), 150))
    concept_list = [{"id": c.id, "title": c.title} for c in sampled_concepts]
    
    system_prompt = (
        "You are an AI logic mapper. Analyze the provided list of academic concepts. "
        "Identify logical prerequisite relationships. (E.g. 'Addition' is a prerequisite to 'Multiplication'). "
        "Return EXACTLY a raw JSON array of paired IDs. Do not write any other markdown. "
        "Format: [{\"child_id\": 10, \"parent_id\": 5}]"
    )

    try:
        response_text = call_ai_completion(
            system_prompt,
            json.dumps(concept_list),
            is_json=True,
            temperature=0.1
        )
        import re
        response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
        match = re.search(r'\[[\s\S]*\]', response_text)
        if match:
            response_text = match.group(0)
        else:
            response_text = "[]"
        import ast
        try:
            pairs = json.loads(response_text)
        except Exception:
            try:
                pairs = ast.literal_eval(response_text)
            except Exception:
                pairs = []
        
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
    concept = db.query(Concept).filter(Concept.id == payload.concept_id, Concept.user_id == current_user.id).first()
    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    system_prompt = (
        "You are a Socratic Tutor. Your job is to compare a student's answer "
        "from memory against the True System Answer. "
        "Evaluate their response strictly for factual correctness, missing nuance, and overall grasp of the material.\n\n"
        "SOCRATIC MODE: If the student's answer is lacking, identify the specific knowledge gap "
        "and generate a targeted follow-up question to help them discover the missing piece themselves.\n\n"
        "Return EXACTLY a raw JSON object formatting using this schema:\n"
        "{\n"
        "  \"sm2_score\": <integer 0 to 5>,\n"
        "  \"fsrs_score\": <integer 1 to 4>,\n"
        "  \"feedback_markdown\": \"<your detailed, encouraging but strict critique of what they missed or got right formatted as markdown>\",\n"
        "  \"confidence_score\": <float 0.0 to 1.0>,\n"
        "  \"follow_up_question\": \"<optional string: a Socratic follow-up if they missed something, else null>\"\n"
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

    # Handle JSON-based Card structure (Front/Back)
    true_answer = concept.content
    display_question = concept.title
    
    try:
        if concept.content and concept.content.strip().startswith('{'):
            parsed = json.loads(concept.content)
            if "front" in parsed and "back" in parsed:
                display_question = f"{concept.title} - {parsed['front']}"
                true_answer = parsed["back"]
    except Exception:
        pass

    user_prompt = f"""
    Flashcard Question / Topic:
    {display_question}

    True System Answer:
    {true_answer}

    Student's Typed Answer:
    {payload.typed_answer}
    """

    try:
        response_text = call_ai_completion(
            system_prompt,
            user_prompt,
            is_json=True,
            temperature=0.1
        )
        import re, ast
        
        # Strip thinking block
        response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
        
        evaluation = {}
        match = re.search(r'\{\s*"sm2_score"[\s\S]*\}', response_text)
        if match:
            candidate = match.group(0)
            try:
                evaluation = json.loads(candidate)
            except Exception:
                try:
                    evaluation = ast.literal_eval(candidate)
                except Exception:
                    pass
                    
        # Fallback to regex-based key extraction if JSON load failed completely
        if not evaluation:
            sm2_m = re.search(r'"sm2_score"\s*:\s*(\d+)', response_text) or re.search(r'sm2_score\s*:\s*(\d+)', response_text)
            fsrs_m = re.search(r'"fsrs_score"\s*:\s*(\d+)', response_text) or re.search(r'fsrs_score\s*:\s*(\d+)', response_text)
            conf_m = re.search(r'"confidence_score"\s*:\s*([0-9.]+)', response_text) or re.search(r'confidence_score\s*:\s*([0-9.]+)', response_text)
            
            feedback_m = re.search(r'"feedback_markdown"\s*:\s*"(.*?)"(?=\s*,|\s*\})', response_text, re.DOTALL)
            if not feedback_m:
                feedback_m = re.search(r"'feedback_markdown'\s*:\s*'(.*?)'(?=\s*,|\s*\})", response_text, re.DOTALL)
            if not feedback_m:
                feedback_m = re.search(r'"feedback_markdown"\s*:\s*"(.*?)"', response_text, re.DOTALL)
                
            followup_m = re.search(r'"follow_up_question"\s*:\s*"(.*?)"(?=\s*,|\s*\})', response_text, re.DOTALL)
            if not followup_m:
                followup_m = re.search(r'"follow_up_question"\s*:\s*"(.*?)"', response_text, re.DOTALL)
                
            if sm2_m: evaluation["sm2_score"] = int(sm2_m.group(1))
            if fsrs_m: evaluation["fsrs_score"] = int(fsrs_m.group(1))
            if conf_m:
                try: evaluation["confidence_score"] = float(conf_m.group(1))
                except: pass
            if feedback_m: evaluation["feedback_markdown"] = feedback_m.group(1).replace('\\"', '"').replace('\\n', '\n')
            if followup_m:
                val = followup_m.group(1).strip()
                evaluation["follow_up_question"] = None if val.lower() == 'null' else val.replace('\\"', '"').replace('\\n', '\n')
            elif 'null' in response_text.lower() and 'follow_up_question' in response_text:
                evaluation["follow_up_question"] = None

        return app.schemas.ai.AIEvaluateResponse(
            sm2_score=evaluation.get("sm2_score", 3),
            fsrs_score=evaluation.get("fsrs_score", 3),
            feedback_markdown=evaluation.get("feedback_markdown", "Failed to parse feedback from AI response."),
            confidence_score=evaluation.get("confidence_score", 0.9),
            follow_up_question=evaluation.get("follow_up_question")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate answer: {str(e)}")


@router.post("/suggest-bridges", response_model=SuggestBridgesResponse)
def suggest_bridges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Identifies 'island' concepts (disconnected from the main graph) 
    and uses AI to suggest 2-3 new bridging concepts to integrate them.
    """

    # Find concepts without any parent or children
    all_concepts = db.query(Concept).filter(Concept.user_id == current_user.id).all()
    
    islands = []
    connected_ids = set()
    
    # Simple check for islands: No parent_concept_id and not a parent to anyone
    for c in all_concepts:
        has_children = db.query(Concept).filter(Concept.parent_concept_id == c.id).first() is not None
        if c.parent_concept_id is None and not has_children:
            islands.append(c)
        else:
            connected_ids.add(c.id)

    if len(islands) < 1 or len(connected_ids) < 1:
        # If everything is connected, or everything is an island, just pick two random concepts
        if len(all_concepts) < 2:
            return SuggestBridgesResponse(suggestions=[])
        source = all_concepts[0]
        target = all_concepts[1]
    else:
        source = random.choice(islands)
        # Try to find a connected concept as target
        target_id = random.choice(list(connected_ids))
        target = db.query(Concept).filter(Concept.id == target_id).first()

    system_prompt = (
        "You are a Knowledge Graph Architect. Your goal is to help students connect distant concepts. "
        "Given two concepts, suggest 2-3 NEW bridging concepts that logically link them together.\n\n"
        "Return EXACTLY a raw JSON array of objects. Do not write any other markdown.\n"
        "Format: [{\"title\": \"Bridge Concept Name\", \"content\": \"Brief explanation of the link\", \"rationale\": \"Why this links A and B\"}]"
    )

    user_prompt = f"""
    Concept A: {source.title} ({source.content})
    Concept B: {target.title} ({target.content})

    Suggest 2 bridging concepts to link these two.
    """

    try:
        response_text = call_ai_completion(
            system_prompt,
            user_prompt,
            is_json=True,
            temperature=0.7
        )
        import re, ast
        response_text = re.sub(r'<think>.*?</think>', '', response_text, flags=re.DOTALL).strip()
        match = re.search(r'\[[\s\S]*\]', response_text)
        if match:
            response_text = match.group(0)
        else:
            response_text = "[]"
        try:
            bridges = json.loads(response_text)
        except Exception:
            try:
                bridges = ast.literal_eval(response_text)
            except Exception:
                bridges = []
        
        suggestions = []
        for b in bridges:
            suggestions.append(BridgeSuggestion(
                title=b.get("title", "Bridge"),
                content=b.get("content", ""),
                source_concept_id=source.id,
                target_concept_id=target.id,
                rationale=b.get("rationale", "")
            ))
            
        return SuggestBridgesResponse(suggestions=suggestions)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to suggest bridges: {str(e)}")


@router.get("/exam-recap/{subject_id}", response_model=ExamRecapResponse)
def get_exam_recap(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates a 'Neural Cheat Sheet' for a 5-minute pre-exam review.
    Aggregates all concepts for the subject and uses AI to summarize them into a high-density recap.
    """
    subject = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == current_user.id).first()
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    concepts = db.query(Concept).filter(Concept.subject_id == subject_id, Concept.user_id == current_user.id).all()
    if not concepts:
        return ExamRecapResponse(recap_markdown="No concepts found for this subject. Add some flashcards first!")

    # Prepare concept data for the prompt
    concept_data = "\n".join([f"- {c.title}: {c.content}" for c in concepts])

    system_prompt = (
        "You are an expert tutor specializing in high-density knowledge retention. "
        "Your goal is to create a 'Neural Cheat Sheet' for a student who has an exam in 5 minutes. "
        "Focus on core principles, tricky nuances, and high-level connections. "
        "Use Markdown for a beautiful, scanable layout with bold headers, bullet points, and 'Recall Triggers'."
    )

    user_prompt = f"""
    Subject: {subject.name}
    
    Here are the concepts the student has been studying:
    {concept_data}

    Based on these, generate a 'Neural Cheat Sheet'. 
    Focus on the most important 'Big Ideas' and the 'Connecting Logic' between them.
    Keep it high-density but scanable for a 5-minute review.
    """

    try:
        content = call_ai_completion(
            system_prompt,
            user_prompt,
            temperature=0.5
        )
        return ExamRecapResponse(recap_markdown=content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recap: {str(e)}")
