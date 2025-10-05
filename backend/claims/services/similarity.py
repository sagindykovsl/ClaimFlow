import faiss
import numpy as np
import json
import os
from .embeddings import embed_texts

INDEX_PATH = os.environ.get("FAISS_INDEX_PATH", "faiss.index")
META_PATH = os.environ.get("FAISS_META_PATH", "faiss_meta.json")

_index = None
_meta = []


def load_index():
    """Load FAISS index and metadata from disk"""
    global _index, _meta
    if os.path.exists(INDEX_PATH):
        _index = faiss.read_index(INDEX_PATH)
    if os.path.exists(META_PATH):
        with open(META_PATH) as f:
            _meta = json.load(f)
    return _index is not None and len(_meta) == (_index.ntotal if _index else 0)


def build_index(claims_texts: list, meta: list):
    """Build FAISS index from texts and metadata"""
    global _index, _meta
    vecs = embed_texts(claims_texts)
    dim = vecs.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine similarity if normalized
    index.add(vecs)
    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "w") as f:
        json.dump(meta, f)
    _index = index
    _meta = meta
    return True


def query_similar(text: str, k=3):
    """Query for similar claims"""
    global _index, _meta
    if _index is None or not _meta:
        if not load_index():
            return []
    if _index is None:
        return []

    q = embed_texts([text])
    scores, idxs = _index.search(q, min(k, _index.ntotal))
    out = []
    for score, idx in zip(scores[0], idxs[0]):
        if idx == -1:
            continue
        m = _meta[idx].copy()
        m["similarity"] = float(score)
        out.append(m)
    return out
