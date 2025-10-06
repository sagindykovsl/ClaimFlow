#!/usr/bin/env python
"""Build FAISS index from past claims data"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "avallon_backend.settings")
django.setup()

import json
from claims.services.similarity import build_index

# Load past claims data
DATA_PATH = os.path.join(os.path.dirname(__file__), "past_claims.json")
with open(DATA_PATH) as f:
    DATA = json.load(f)

# Extract texts and metadata
texts = [d["transcript"] for d in DATA]
meta = [{"id": d["id"], "label": d["label"], "preview": d["transcript"][:120]} for d in DATA]

# Build index
print(f"Building FAISS index from {len(texts)} past claims...")
ok = build_index(texts, meta)
print(f"Index built successfully: {ok}")
print("Index saved to: faiss.index")
print("Metadata saved to: faiss_meta.json")
