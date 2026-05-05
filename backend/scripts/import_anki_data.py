import sys
import os
import pandas as pd
import random
from datetime import datetime, timezone
from freezegun import freeze_time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

def run_import():
    # 1. Read the Anki Dataset
    csv_file = "anki_sample.csv"
    if not os.path.exists(csv_file):
        print(f"File {csv_file} not found. Please download the dataset and place it here.")
        return
        
    print(f"Loading Anki dataset from {csv_file}...")
    df = pd.read_csv(csv_file)
    
    # 2. Set up the Database & User
    db = SessionLocal()
    user = db.query(User).filter(User.username == "prasad2").first()
    
    if not user:
        print("Creating user prasad2...")
        user = User(
            username="prasad2",
            email="prasad2@anki.com",
            password_hash=hash_password("123456")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        print("User prasad2 already exists. Cleaning up old data...")
        db.query(SchedulingData).filter(SchedulingData.user_id == user.id).delete()
        db.query(ConceptEdge).filter(ConceptEdge.user_id == user.id).delete()
        from app.models.review_log import ReviewLog
        from app.models.propagation_log import PropagationLog
        db.query(ReviewLog).filter(ReviewLog.user_id == user.id).delete()
        db.query(PropagationLog).filter(PropagationLog.user_id == user.id).delete()
        db.query(Concept).filter(Concept.user_id == user.id).delete()
        db.query(Subject).filter(Subject.user_id == user.id).delete()
        db.commit()

    # 3. Create dummy Subject
    subject = Subject(name="Anki Real-World Dataset", description="Concepts imported from Anki 10k log", user_id=user.id)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    
    # 4. Map Anki Cards to Concepts
    unique_cards = df['card_id'].unique()
    print(f"Mapping {len(unique_cards)} unique Anki cards to Concepts...")
    
    card_map = {} # Maps Anki card_id to our Concept ID
    prev_concept = None
    
    for idx, cid in enumerate(unique_cards):
        algo = ["sm2", "fsrs", "multi_fsrs"][idx % 3]
        
        concept = Concept(
            subject_id=subject.id,
            user_id=user.id,
            title=f"Anki Card #{cid}",
            content=f"Historical data imported for card {cid}.",
            difficulty="medium",
            parent_concept_id=prev_concept.id if prev_concept else None
        )
        db.add(concept)
        db.flush()
        
        card_map[cid] = concept
        
        # Initial SchedulingData with an old date (so it's "due" when the first log happens)
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
            next_review_date=datetime.now(timezone.utc) - pd.Timedelta(days=100)
        )
        db.add(sched)
        
        if prev_concept:
            try:
                GraphManager.add_edge(db, user.id, prev_concept.id, concept.id, w_expert=0.5)
            except ValueError:
                pass
                
        prev_concept = concept
        db.commit()
        
    # 5. Replay the History!
    print(f"Replaying {len(df)} historical review logs through the algorithmic pipeline...")
    
    success_count = 0
    for index, row in df.iterrows():
        # Anki review_id is epoch milliseconds
        timestamp = datetime.fromtimestamp(row['review_id'] / 1000.0, tz=timezone.utc)
        anki_rating = int(row['review_rating']) # 1-4
        duration_sec = int(row.get('review_time', 5000)) / 1000.0
        
        concept = card_map[row['card_id']]
        
        with freeze_time(timestamp):
            sched = db.query(SchedulingData).filter(SchedulingData.concept_id == concept.id).first()
            if not sched:
                continue
                
            payload = ReviewSubmit(
                concept_id=concept.id,
                quality_score=anki_rating,
                response_time_sec=duration_sec,
                was_correct=anki_rating >= 3
            )
            
            process_review(db, user, concept, sched, payload)
            success_count += 1
            
            if success_count % 50 == 0:
                print(f"Replayed {success_count}/{len(df)} logs...")

    print("\n✅ Import Complete! The dashboard is populated with authentic learning curves.")
    print("You can now log in as prasad2 / 123456.")
    db.close()

if __name__ == "__main__":
    run_import()
