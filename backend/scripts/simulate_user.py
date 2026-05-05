import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import random
from datetime import datetime, timedelta, timezone
from freezegun import freeze_time
from sqlalchemy.orm import Session

# Ensure tables are created
from app.database import SessionLocal, Base, engine
Base.metadata.create_all(bind=engine)

from app.models.user import User
from app.models.subject import Subject
from app.models.concept import Concept
from app.models.scheduling import SchedulingData
from app.models.concept_edge import ConceptEdge
from app.utils.auth import hash_password
from app.algorithms.knowledge_graph import GraphManager
from app.services.review_service import process_review
from app.schemas.review import ReviewSubmit

SUBJECTS_DATA = {
    "Machine Learning": [
        "Linear Regression", "Logistic Regression", "Gradient Descent", "Backpropagation", 
        "Decision Trees", "Random Forest", "Ensemble Methods", "Naive Bayes", "K-Means", "PCA", 
        "SVM", "Neural Networks", "CNNs", "RNNs", "Transformers", "Dropout", "Batch Normalization", 
        "Adam Optimizer", "Word2Vec", "GANs"
    ],
    "Data Structures & Algorithms": [
        "Arrays", "Linked Lists", "Stacks", "Queues", "Hash Tables", "Binary Trees", "BST", 
        "AVL Trees", "Red-Black Trees", "Heaps", "Trie", "Graphs", "BFS", "DFS", "Dijkstra's", 
        "A*", "Bellman-Ford", "Kruskal's", "Prim's", "Dynamic Programming"
    ],
    "C++": [
        "Pointers", "References", "Classes", "Objects", "Constructors", "Destructors", 
        "Virtual Functions", "Polymorphism", "Inheritance", "Templates", "STL", "Smart Pointers", 
        "Move Semantics", "Lambda Expressions", "Exception Handling", "RAII", "Namespaces", 
        "Operator Overloading", "Friend Functions", "Constexpr"
    ],
    "Object Oriented Programming": [
        "Encapsulation", "Abstraction", "Inheritance", "Polymorphism", "SOLID", 
        "Single Responsibility", "Open/Closed", "Liskov Substitution", "Interface Segregation", 
        "Dependency Inversion", "DRY", "KISS", "YAGNI", "Composition", "Aggregation", 
        "Association", "Interfaces", "Abstract Classes", "Design Patterns", "Singleton"
    ],
    "Operating Systems": [
        "Processes", "Threads", "Scheduling", "Context Switch", "Deadlocks", "Mutex", 
        "Semaphores", "Monitors", "Virtual Memory", "Paging", "Segmentation", "Thrashing", 
        "File Systems", "Inodes", "I/O Management", "Interrupts", "System Calls", "IPC", 
        "Pipes", "Sockets"
    ],
    "Digital Electronics": [
        "Boolean Algebra", "Logic Gates", "K-Maps", "Combinational Circuits", "Sequential Circuits", 
        "Adders", "Subtractors", "Multiplexers", "Demultiplexers", "Encoders", "Decoders", 
        "Flip-Flops", "Latches", "Registers", "Counters", "State Machines", "RAM", "ROM", 
        "FPGA", "Microprocessors"
    ]
}

def simulate():
    db = SessionLocal()
    
    # 1. Create or get user
    user = db.query(User).filter(User.username == "prasad1").first()
    if not user:
        print("Creating user prasad1...")
        user = User(
            username="prasad1",
            email="prasad1@example.com",
            password_hash=hash_password("123456")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        print("User prasad1 already exists. Cleaning up old data...")
        # Clean up old data for simulation
        db.query(SchedulingData).filter(SchedulingData.user_id == user.id).delete()
        db.query(ConceptEdge).filter(ConceptEdge.user_id == user.id).delete()
        from app.models.review_log import ReviewLog
        from app.models.propagation_log import PropagationLog
        db.query(ReviewLog).filter(ReviewLog.user_id == user.id).delete()
        db.query(PropagationLog).filter(PropagationLog.user_id == user.id).delete()
        db.query(Concept).filter(Concept.user_id == user.id).delete()
        db.query(Subject).filter(Subject.user_id == user.id).delete()
        db.commit()

    start_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    print("Setting up subjects and concepts...")
    # Freeze time to 30 days ago for creation
    with freeze_time(start_date):
        for subj_name, concepts in SUBJECTS_DATA.items():
            subject = Subject(name=subj_name, description=f"Comprehensive course on {subj_name}", user_id=user.id)
            db.add(subject)
            db.commit()
            db.refresh(subject)
            
            prev_concept = None
            for idx, c_title in enumerate(concepts):
                # Distribute algorithms evenly
                algo = ["sm2", "fsrs", "multi_fsrs"][idx % 3]
                
                concept = Concept(
                    subject_id=subject.id,
                    user_id=user.id,
                    title=c_title,
                    content=f"Detailed study notes and explanation for {c_title}.",
                    difficulty=random.choice(["easy", "medium", "hard"]),
                    parent_concept_id=prev_concept.id if prev_concept else None
                )
                db.add(concept)
                db.flush()
                
                # Sched data
                sched = SchedulingData(
                    concept_id=concept.id,
                    user_id=user.id,
                    algorithm=algo,
                    ease_factor=2.5,
                    interval_days=1,
                    repetitions=0,
                    stability=0.0,
                    difficulty_fsrs=5.0,
                    retrievability=1.0,
                    next_review_date=start_date
                )
                db.add(sched)
                
                # Knowledge graph edge (chaining them together)
                if prev_concept:
                    try:
                        GraphManager.add_edge(db, user.id, prev_concept.id, concept.id, w_expert=0.6)
                    except ValueError:
                        pass
                
                prev_concept = concept
                db.commit()
    
    # 2. Simulate 30 days of reviews
    print("Simulating 30 days of learning...")
    
    for day in range(30):
        current_sim_date = start_date + timedelta(days=day)
        
        with freeze_time(current_sim_date):
            # Find due concepts for today
            due_scheds = (
                db.query(SchedulingData)
                .filter(
                    SchedulingData.user_id == user.id,
                    SchedulingData.next_review_date <= current_sim_date
                )
                .all()
            )
            
            # Simulate user reviewing up to 40 cards a day
            to_review = due_scheds[:40]
            
            success_count = 0
            for sched in to_review:
                concept = db.query(Concept).filter(Concept.id == sched.concept_id).first()
                
                # Simulate a quality score (1-4 for FSRS, 0-5 for SM2)
                # Let's bias towards remembering (score 3 or 4 mostly)
                rand_val = random.random()
                if sched.algorithm == "sm2":
                    if rand_val < 0.1: score = random.choice([0, 1, 2])
                    elif rand_val < 0.4: score = 3
                    elif rand_val < 0.8: score = 4
                    else: score = 5
                else:
                    if rand_val < 0.1: score = 1
                    elif rand_val < 0.3: score = 2
                    elif rand_val < 0.8: score = 3
                    else: score = 4
                
                payload = ReviewSubmit(
                    concept_id=concept.id,
                    quality_score=score,
                    response_time_sec=random.randint(5, 30),
                    was_correct=(score >= 3 if sched.algorithm == "sm2" else score >= 3)
                )
                
                # Important: process_review uses datetime.now(), which is mocked by freezegun!
                process_review(db, user, concept, sched, payload)
                success_count += 1
            
            print(f"Day {day + 1}/30 [{current_sim_date.strftime('%Y-%m-%d')}]: Reviewed {success_count} concepts.")

    print("\nSimulation complete! You can now log in as prasad1 / 123456.")
    db.close()

if __name__ == "__main__":
    simulate()
