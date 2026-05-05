import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# Create 50 unique card IDs
card_ids = [10000 + i for i in range(50)]

logs = []
start_date = datetime.now() - timedelta(days=60)

for cid in card_ids:
    current_date = start_date + timedelta(days=random.randint(0, 5))
    interval = 1
    state = 0  # new
    
    # Simulate 5-15 reviews per card over the 60 days
    num_reviews = random.randint(5, 15)
    for _ in range(num_reviews):
        # Determine rating
        # If interval is large, maybe hard. If small, mostly good/easy.
        rand = random.random()
        if rand < 0.1:
            rating = 1  # Again
            interval = 1
            state = 3  # relearning
        elif rand < 0.3:
            rating = 2  # Hard
            interval = max(1, int(interval * 1.2))
            state = 2  # review
        elif rand < 0.8:
            rating = 3  # Good
            interval = max(1, int(interval * 2.5))
            state = 2
        else:
            rating = 4  # Easy
            interval = max(1, int(interval * 3.5))
            state = 2
            
        logs.append({
            "review_id": int(current_date.timestamp() * 1000),
            "card_id": cid,
            "review_time": random.randint(3000, 15000), # 3-15 seconds
            "review_rating": rating,
            "review_state": state
        })
        
        current_date += timedelta(days=interval)
        if current_date > datetime.now():
            break

df = pd.DataFrame(logs)
df.sort_values("review_id", inplace=True)
df.to_csv("anki_sample.csv", index=False)
print("Generated anki_sample.csv with", len(df), "simulated historical reviews matching Anki schema.")
