from sentence_transformers import SentenceTransformer
import numpy as np

_model = None


def get_model():
    """Load and cache the embedding model"""
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def embed_texts(texts: list) -> np.ndarray:
    """Embed a list of texts into vectors"""
    model = get_model()
    vecs = model.encode(texts, normalize_embeddings=True)
    return np.array(vecs, dtype="float32")
