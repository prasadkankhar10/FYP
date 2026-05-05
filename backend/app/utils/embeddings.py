"""
utils/embeddings.py — Semantic Embeddings utility.
Uses HuggingFace sentence-transformers to calculate cosine similarity
between concept contents. This is used to automatically populate `w_semantic`
for the Multi-Concept FSRS Knowledge Graph.
"""
from typing import Optional
import numpy as np

# We load the model lazily so it doesn't block server startup
_model = None

def get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            # all-MiniLM-L6-v2 is extremely fast, small (~80MB), and good for English semantics
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            print("WARNING: sentence-transformers not installed. Semantic weights will be 0.")
            return None
        except Exception as e:
            print(f"ERROR: Failed to load sentence-transformers model: {e}")
            return None
    return _model

def compute_similarity(text1: Optional[str], text2: Optional[str]) -> float:
    """
    Compute cosine similarity between two text strings.
    Returns a float between 0.0 and 1.0.
    """
    if not text1 or not text2:
        return 0.0

    model = get_model()
    if not model:
        return 0.0

    try:
        from sentence_transformers import util
        
        # Encode texts to get their embeddings
        emb1 = model.encode(text1, convert_to_tensor=True)
        emb2 = model.encode(text2, convert_to_tensor=True)
        
        # Compute cosine similarity
        cosine_scores = util.cos_sim(emb1, emb2)
        
        # Convert to float and clamp to [0.0, 1.0]
        # (Cosine similarity can theoretically be -1 to 1)
        similarity = float(cosine_scores[0][0].item())
        return max(0.0, min(1.0, similarity))
    except Exception as e:
        print(f"ERROR: Failed to compute similarity: {e}")
        return 0.0
