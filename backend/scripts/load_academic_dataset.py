"""
scripts/load_academic_dataset.py — Data ingestion script for academic benchmarking.
Loads ONE deep user, randomized algorithms, rich semantic edges, and calculates true FSRS.
"""
import sys
import os
import random
from datetime import datetime, timezone, timedelta

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, init_db
from app.utils.auth import hash_password
from app.models.user import User
from app.models.subject import Subject
from app.models.concept import Concept
from app.models.concept_edge import ConceptEdge
from app.models.review_log import ReviewLog
from app.models.scheduling import SchedulingData
from app.algorithms.multi_fsrs import calculate as multi_fsrs_calculate
from app.algorithms.fsrs import calculate as fsrs_calculate
from app.algorithms.sm2 import calculate as sm2_calculate
from app.algorithms.knowledge_graph import GraphManager


# ──────────────────────────────────────────────────────────────────────────────
# DATA DEFINITIONS
# ──────────────────────────────────────────────────────────────────────────────

CONCEPTS_DATA = [
    (101, "What is a variable?", "A container for storing data values.", "Programming Basics"),
    (102, "What is a data type?", "A classification of data such as int float or string.", "Programming Basics"),
    (103, "What is an operator?", "A symbol used to perform operations on variables and values.", "Programming Basics"),
    (104, "What is a conditional statement?", "A statement that executes code based on a condition.", "Programming Basics"),
    (105, "What is a loop?", "A control structure that repeats code multiple times.", "Programming Basics"),
    (106, "What is a function?", "A reusable block of code that performs a task.", "Programming Basics"),
    (107, "What is a parameter?", "An input passed into a function.", "Programming Basics"),
    (108, "What is a return value?", "The output produced by a function.", "Programming Basics"),
    (109, "What is scope?", "The region where a variable is accessible.", "Programming Basics"),
    (110, "What is recursion?", "A function calling itself to solve a problem.", "Programming Basics"),
    (111, "What is an array?", "A collection of elements stored in contiguous memory.", "Programming Basics"),
    (112, "What is an index?", "The position of an element in an array.", "Programming Basics"),
    (113, "What is a pointer?", "A variable that stores a memory address.", "Programming Basics"),
    (114, "What is dynamic memory?", "Memory allocated during runtime.", "Programming Basics"),
    (115, "What is a class?", "A blueprint for creating objects.", "OOP"),
    (116, "What is an object?", "An instance of a class.", "OOP"),
    (117, "What is inheritance?", "A mechanism where one class derives from another.", "OOP"),
    (118, "What is polymorphism?", "Ability of objects to take multiple forms.", "OOP"),
    (119, "What is abstraction?", "Hiding implementation details and showing essentials.", "OOP"),
    (120, "What is encapsulation?", "Bundling data and methods within a class.", "OOP")
]

# Baseline logs provided by user for User 1
BASE_LOGS = [
    (101,1704067200,1,14), (106,1704068200,1,16), (102,1704153600,2,11),
    (101,1704240000,2,9), (106,1704241000,2,12), (103,1704326400,3,8),
    (104,1704412800,2,10), (101,1704499200,3,6), (106,1704499800,3,7),
    (107,1704585600,2,9), (108,1704672000,2,8), (101,1704758400,4,4),
    (106,1704759000,4,5), (110,1704844800,2,10), (110,1705027600,3,7),
    (110,1705200400,4,4)
]

def generate_deep_logs():
    """Generates ~250 review logs for ONE user spanning 2 months."""
    logs = list(BASE_LOGS)
    
    base_ts = 1705700000 
    
    # Simulating 60 days of reviews
    for day in range(60):
        ts = base_ts + (day * 86400)
        
        # Pick 3-5 random concepts to review today
        num_reviews = random.randint(3, 5)
        concepts_to_review = random.sample(range(101, 121), num_reviews)
        
        for i, c_id in enumerate(concepts_to_review):
            review_ts = ts + (i * 3600)
            
            # Simulate natural grade improvement over time
            # Later days = higher grades, lower response times
            if day < 10:
                grade = random.choice([1, 2, 3])
                resp = random.randint(10, 20)
            elif day < 30:
                grade = random.choice([2, 3, 3, 4])
                resp = random.randint(6, 12)
            else:
                grade = random.choice([3, 4, 4, 4])
                resp = random.randint(3, 8)
                
            logs.append((c_id, review_ts, grade, resp))

    return sorted(logs, key=lambda x: x[1]) # Sort chronologically


def main():
    # Drop all tables first to completely wipe the old data
    from app.database import Base, engine
    Base.metadata.drop_all(bind=engine)
    
    db: Session = SessionLocal()
    init_db()
    
    print("==================================================")
    print(" 📚 STARTING DEEP ACADEMIC DATASET INGESTION")
    print("==================================================")

    email = "research_student1@example.com"


    # 2. Create User
    print("[2/5] Creating Deep Research User...")
    pw_hash = hash_password("123456")
    u = User(username="research1", email=email, password_hash=pw_hash)
    db.add(u)
    db.commit()
    db.refresh(u)
    db_user_id = u.id

    # 3. Create Subjects & Concepts
    print("[3/5] Creating Subjects & Concepts with Random Algorithms...")
    concept_map = {} # CSV item_id -> DB concept_id
    algorithms = ["sm2", "fsrs", "multi_fsrs"]
    
    sub_basics = Subject(name="Programming Basics", user_id=db_user_id)
    sub_oop = Subject(name="Object-Oriented Programming", user_id=db_user_id)
    db.add(sub_basics)
    db.add(sub_oop)
    db.commit()
    db.refresh(sub_basics)
    db.refresh(sub_oop)
    
    for c_id, front, back, sub_name in CONCEPTS_DATA:
        sub_id = sub_basics.id if sub_name == "Programming Basics" else sub_oop.id
        c = Concept(
            user_id=db_user_id,
            subject_id=sub_id,
            title=front, # UI FIX: Show the actual question
            content=f"Q: {front}\nA: {back}"
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        concept_map[c_id] = c.id
        
        algo = random.choice(algorithms)
        sched = SchedulingData(user_id=db_user_id, concept_id=c.id, algorithm=algo)
        db.add(sched)
    db.commit()

    # 4. FIXED LOGICAL Graph Construction
    print("[4/5] Building LOGICAL Graph Edges (Computing Semantic Weights)...")
    
    logical_edges = [
        # Programming Basics
        (101, 102), (101, 103), (101, 109), # Variable -> Data Type, Operator, Scope
        (104, 105),                         # Conditional -> Loop
        (105, 111),                         # Loop -> Array
        (111, 112),                         # Array -> Index
        (106, 107), (106, 108), (106, 110), # Function -> Parameter, Return Value, Recursion
        (111, 113), (113, 114),             # Array -> Pointer -> Dynamic Memory
        
        # OOP
        (115, 116), (115, 117), (115, 120), (115, 119), # Class -> Object, Inheritance, Encapsulation, Abstraction
        (117, 118),                                     # Inheritance -> Polymorphism
        
        # Cross-Domain
        (102, 115), # Data Type -> Class
        (106, 120)  # Function -> Encapsulation
    ]
    
    for source, target in logical_edges:
        try:
            GraphManager.add_edge(
                db, 
                db_user_id, 
                concept_map[source], 
                concept_map[target], 
                w_expert=0.8
            )
        except ValueError:
            pass # Ignore if it hits any theoretical limits


    # 5. Ingest Review Logs chronologically
    logs = generate_deep_logs()
    print(f"[5/5] Propagating {len(logs)} chronological review logs through engines...")
    
    processed = 0
    for c_id, ts, grade, resp_time in logs:
        db_concept_id = concept_map[c_id]
        review_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        
        sched = db.query(SchedulingData).filter(SchedulingData.concept_id == db_concept_id).first()
        concept = db.query(Concept).filter(Concept.id == db_concept_id).first()
        
        # Calculate R
        last_dt = sched.last_review_date.replace(tzinfo=timezone.utc) if sched.last_review_date else None
        days_since = (review_dt - last_dt).days if last_dt else 0
        r_val = 1.0
        if sched.stability > 0:
            import math
            r_val = math.pow(1 + max(0, days_since) / (9 * sched.stability), -1)
            
        # Log it
        log = ReviewLog(
            user_id=db_user_id,
            concept_id=db_concept_id,
            algorithm_used=sched.algorithm,
            quality_score=grade,
            response_time_sec=resp_time,
            was_correct=(grade > 1),
            retention_at_review=r_val,
            reviewed_at=review_dt
        )
        db.add(log)
        
        # Execute the correct engine
        if sched.algorithm == "multi_fsrs":
            updated = multi_fsrs_calculate(sched, grade, concept, db)
        elif sched.algorithm == "fsrs":
            updated = fsrs_calculate(sched, grade)
        else:
            updated = sm2_calculate(sched, grade)
            
        for k, v in updated.items():
            if hasattr(sched, k):
                setattr(sched, k, v)
        sched.last_review_date = review_dt
        
        db.commit()
        processed += 1
        if processed % 50 == 0:
            print(f"  ...processed {processed}/{len(logs)} reviews.")

    print("\n✅ DEEP DATASET SUCCESSFULLY INGESTED!")
    print("--------------------------------------------------")
    print("Login Details:")
    print("Email: research_student1@example.com")
    print("Password: 123456")
    print("--------------------------------------------------")

if __name__ == "__main__":
    main()
