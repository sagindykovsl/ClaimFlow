# ClaimFlow - Summary

A Voice-Enabled Claim Processing Simulator that uses **pure LLM-based extraction** via LangChain and **FAISS vector similarity search** to process insurance claims.

## How It Works

### 🔄 Complete Data Flow

```
USER SUBMITS CLAIM
        ↓
┌───────────────────────────────────────────────────────┐
│ STEP 1: LLM EXTRACTION (6 prompt chains)             │
├───────────────────────────────────────────────────────┤
│  Transcript → LangChain FLAN-T5-base                  │
│                                                        │
│  1. Extract name: "Aigerim Zhanatova"                 │
│  2. Extract phone: "8-701-234-5678"                   │
│  3. Extract date: "September 2, 2024"                 │
│  4. Extract location: "Almaty"                        │
│  5. Extract amount: "350000"                          │
│  6. Generate summary: "Rear-ended, bumper damage..."  │
│                                                        │
│  Anti-hallucination validation ✓                      │
└───────────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────────┐
│ STEP 2: CLASSIFICATION (LLM + Rules)                  │
├───────────────────────────────────────────────────────┤
│  Score calculation:                                    │
│  - Base: 1.0                                           │
│  - Missing fields: -0.25 each                          │
│  - Fraud indicators (via LLM): -0.3 each               │
│                                                        │
│  Fraud detection (LangChain):                          │
│  "Does caller not remember details?" → YES/NO          │
│  "Are documents missing?" → YES/NO                     │
│  "Calling for someone else?" → YES/NO                  │
│                                                        │
│  Label: valid/invalid/fraudulent                       │
│  Score: 0.0-1.0                                        │
└───────────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────────┐
│ STEP 3: FAISS SIMILARITY SEARCH                       │
├───────────────────────────────────────────────────────┤
│  Transcript → SentenceTransformer embedding           │
│              → 384-dim vector                          │
│              → FAISS index search (k=3)                │
│              → Find 3 most similar past claims         │
│                                                        │
│  Results:                                              │
│  - c1: 86.6% similar (valid, car accident)            │
│  - c15: 59.4% similar (valid, collision)              │
│  - c10: 58.5% similar (valid, property damage)        │
└───────────────────────────────────────────────────────┘
        ↓
┌───────────────────────────────────────────────────────┐
│ STEP 4: SAVE & RETURN                                 │
├───────────────────────────────────────────────────────┤
│  Save to database:                                     │
│  - Claim record with all extracted data                │
│  - Classification results                              │
│  - Similar claims list                                 │
│                                                        │
│  Return JSON API response                              │
└───────────────────────────────────────────────────────┘
```

---

## Test Results

### Test 1: Complete Valid Claim ✅

**Input:**
```
"Hi, this is Aigerim Zhanatova. I was rear-ended on September 2, 2024 around 5pm near Almaty.
Damage to rear bumper, estimate is 350000 KZT. My phone is 8-701-234-5678"
```

**Extracted:**
- ✅ Name: Aigerim Zhanatova
- ✅ Phone: 8-701-234-5678
- ✅ Date: September 2, 2024
- ✅ Location: Almaty
- ✅ Amount: 350000.0 KZT

**Classification:**
- Label: **valid**
- Score: **1.0** (perfect)
- Flags: None
- Next steps: approve_claim, schedule_assessment

**Similar Claims (FAISS):**
- c1: 86.6% similar (valid, identical scenario)
- c15: 59.4% similar (valid, car collision)
- c10: 58.5% similar (valid, property damage)

---

### Test 2: Incomplete Fraudulent Claim ✅

**Input:**
```
"a pipe burst in my apartment causing water damage"
```

**Extracted:**
- ❌ Name: None
- ❌ Phone: None (hallucination prevented)
- ❌ Date: None
- ❌ Location: None
- ❌ Amount: None
- ✅ Description: "A pipe burst in my apartment causing water damage."

**Classification:**
- Label: **fraudulent**
- Score: **0.2**
- Flags: missing_claimant_name, missing_amount, missing_date
- Next steps: escalate_to_fraud_team, request_police_report

**Similar Claims:**
- c2: 51.5% similar (valid, water damage with full details)

---

## Architecture

### Backend Stack
- **Django 5.2** - REST API framework
- **Django REST Framework** - Serializers, ViewSets
- **SQLite** - Database with JSONField for flexible schema
- **LangChain** - LLM orchestration and prompt chaining
- **transformers** - Local FLAN-T5 model inference
- **sentence-transformers** - Text embedding for FAISS
- **FAISS** - Vector similarity search

### LLM Integration
- **Model**: google/flan-t5-base (220M params, 250MB)
- **Interface**: LangChain HuggingFacePipeline wrapper
- **Approach**: Pure LLM extraction (6 prompt chains)
- **Inference**: Local CPU (1-2s per prompt, ~10s total)

### Vector Search
- **Embedding model**: all-MiniLM-L6-v2 (384 dimensions)
- **Index type**: FAISS IndexFlatL2 (exact search)
- **Dataset**: 20 past claims
- **Search time**: <1ms per query

---

## API Endpoints

### POST /api/claims/
Create new claim from transcript

**Request:**
```json
{
    "transcript": "Hi, this is Aigerim Zhanatova. I was rear-ended..."
}
```

**Response:**
```json
{
    "id": 49,
    "transcript": "...",
    "extracted": {
        "claimant_name": "Aigerim Zhanatova",
        "contact_phone": "8-701-234-5678",
        "incident_datetime": "September 2, 2024",
        "incident_location": "Almaty",
        "claimed_amount": 350000.0,
        "incident_description": "...",
        "metadata": {
            "extraction_method": "langchain_pure_llm",
            "detected_entities": ["claimant_name", "contact_phone", ...]
        }
    },
    "classification": {
        "label": "valid",
        "score": 1.0,
        "rationale": "Completeness: 1.0/1.0. No red flags detected.",
        "policy_flags": [],
        "suggested_next_steps": ["approve_claim", "schedule_assessment"]
    },
    "similar": [
        {
            "id": "c1",
            "label": "valid",
            "similarity": 0.866,
            "preview": "Hi, this is Aigerim Zhanatova..."
        }
    ],
    "status": "analysed",
    "created_at": "2025-10-06T17:31:19Z"
}
```

### POST /api/claims/{id}/action/
Take action on claim (approve/deny/escalate)

### GET /api/claims/
List all claims

---

## File Structure

```
ClaimFlow/
├── backend/
│   ├── claims/
│   │   ├── models.py              # Claim, EmailLog models
│   │   ├── views.py               # API endpoints
│   │   ├── serializers.py         # DRF serializers
│   │   └── services/
│   │       ├── llm.py            # ★ LangChain 6-step prompt chain
│   │       └── similarity.py     # ★ FAISS vector search
│   ├── scripts/
│   │   ├── past_claims.json      # ★ 20 claims (no policy numbers)
│   │   └── build_faiss.py        # FAISS index builder
│   ├── faiss.index               # Binary vector index
│   ├── faiss_meta.json           # Claim metadata
│   └── db.sqlite3                # Database
│
├── LANGCHAIN_EXPLANATION.md       # ★ Pure LLM extraction guide
├── FAISS_VECTOR_SEARCH_EXPLANATION.md  # ★ Vector search guide

```

**★ = Key files to review**

---

## Performance

| Metric | Value |
|--------|-------|
| LLM inference (6 prompts) | ~10 seconds |
| FAISS search | <1ms |
| Total API response time | ~10 seconds |
| Model size (FLAN-T5) | 250MB |
| Model size (embeddings) | 80MB |
| Index size (20 claims) | 30KB |
| Memory usage | ~1GB RAM |

---

## Task Requirements ✅

### Original Task
> "Integrate an LLM (via Hugging Face or LangChain) for natural language understanding—e.g., extract entities and classify claim validity (valid/invalid/fraudulent) using prompt chaining."

**✅ Implemented:**
- LangChain integration with HuggingFacePipeline
- 6-step prompt chain for entity extraction
- LLM-based fraud detection
- Classification: valid/invalid/fraudulent

> "Add a simple embedding search against a vector store (e.g., FAISS with sample past claims) to flag similar cases."

**✅ Implemented:**
- FAISS vector search
- sentence-transformers embeddings
- 20 sample past claims
- k=3 similar claims returned with each submission

---

## Running the System

### 1. Start Backend
```bash
cd backend
source ../.venv/bin/activate
python manage.py runserver
```

### 2. Submit Claim
```bash
curl -X POST http://localhost:8000/api/claims/ \
  -H "Content-Type: application/json" \
  -d '{"transcript":"Your claim text here..."}'
```

### 3. Rebuild FAISS Index (if claims updated)
```bash
python scripts/build_faiss.py
```

---
