"""
scripts/backfill_semantic_weights.py — Standalone script to backfill w_semantic on old edges.
Usage:
    cd backend
    python scripts/backfill_semantic_weights.py
"""
import sys
import os

# Add backend directory to path so we can import 'app'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models.concept import Concept
from app.models.concept_edge import ConceptEdge
from app.utils.embeddings import compute_similarity
from app.algorithms.knowledge_graph import GraphManager

def run_backfill():
    db = SessionLocal()
    print("=" * 60)
    print("  SEMANTIC WEIGHT BACKFILL SCRIPT")
    print("=" * 60)

    # Find edges where w_semantic is exactly 0.0
    edges = db.query(ConceptEdge).filter(ConceptEdge.w_semantic == 0.0).all()
    total = len(edges)
    
    if total == 0:
        print("✅ No edges found requiring a semantic backfill. Everything is up to date!")
        db.close()
        return

    print(f"🔍 Found {total} edges requiring semantic weight computation. Starting...")
    
    updated_count = 0
    for i, edge in enumerate(edges, 1):
        source = db.query(Concept).filter(Concept.id == edge.source_concept_id).first()
        target = db.query(Concept).filter(Concept.id == edge.target_concept_id).first()
        
        if source and target:
            text1 = f"{source.title} {source.content or ''}"
            text2 = f"{target.title} {target.content or ''}"
            
            similarity = compute_similarity(text1, text2)
            edge.w_semantic = similarity
            
            # Recalculate w_final using the GraphManager
            GraphManager.update_edge_w_final(edge)
            
            updated_count += 1
            
            if i % 10 == 0 or i == total:
                print(f"⏳ Processed {i}/{total} edges...")

    # We must also re-normalize the outgoing weights for all affected nodes
    print("⚖️  Normalizing outgoing weights for all affected nodes...")
    affected_nodes = list(set([e.source_concept_id for e in edges] + [e.target_concept_id for e in edges]))
    # Since nodes might belong to different users, we need to handle that.
    # Group by (user_id, concept_id)
    user_concept_pairs = list(set([(e.user_id, e.source_concept_id) for e in edges] + [(e.user_id, e.target_concept_id) for e in edges]))
    
    for user_id, concept_id in user_concept_pairs:
        GraphManager.normalize_outgoing_weights(db, concept_id, user_id)

    db.commit()
    print(f"🎉 Success! Backfilled {updated_count} edges and normalized weights.")
    db.close()

if __name__ == "__main__":
    run_backfill()
