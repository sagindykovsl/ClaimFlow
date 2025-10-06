# ClaimFlow - Voice-Enabled Claim Processing Simulator

An AI-powered insurance claim processing system that simulates voice-to-text claim intake with intelligent entity extraction, fraud detection, and similarity matching.

## Features

- **Entity Extraction**: Automatically extracts structured fields (claimant name, policy number, incident details, amounts) from free-text transcripts using LLM
- **Fraud Classification**: AI-powered classification (valid/invalid/fraudulent) with confidence scores and rationales
- **Similarity Search**: FAISS-powered vector search to find similar past claims
- **Workflow Actions**: Approve, deny, or escalate claims with automated notification tracking
- **Modern UI**: Clean Next.js interface with real-time results display
- **API Documentation**: Auto-generated OpenAPI docs with Swagger UI

## Tech Stack

### Backend
- **Django 5.2** + Django REST Framework
- **SQLite** with JSONField for flexible claim storage
- **LangChain + Transformers (local)** using `google/flan-t5-base` for extraction/classification
- **sentence-transformers** + **FAISS** for similarity search
- **pytest** for testing

### Frontend
- **Next.js 15** (App Router)
- **TypeScript** + **Tailwind CSS v4**
- **axios** for API communication

### DevOps
- **GitHub Actions** CI for automated testing and linting (backend + frontend jobs)
- **ruff**, **black**, **isort** for code quality
- AI decision logging printed to server logs (visible locally and in CI)

## Prerequisites

- Python 3.10+
- Node.js 20+
- No HuggingFace token required (LLM runs locally via Transformers)

## Quick Start

### 1. Clone and Setup Environment

```bash
git clone <repo-url>
cd ClaimFlow

# Create .env file
cp .env.example .env
# Edit .env and add your HF_TOKEN
```

### 2. Backend Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install django djangorestframework django-cors-headers drf-spectacular \
            pydantic python-dotenv transformers sentence-transformers faiss-cpu \
            langchain langchain-huggingface \
            black isort ruff pytest pytest-django

# Setup database
cd backend
python manage.py migrate

# Build FAISS index from seed data
python scripts/build_faiss.py

# Run development server
python manage.py runserver 8000
```

Backend API will be available at `http://localhost:8000/api/`

API Documentation: `http://localhost:8000/api/docs/`

### 3. Frontend Setup

```bash
# In a new terminal
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:3000`

## Usage

1. Open `http://localhost:3000` in your browser
2. Paste a claim transcript in the textarea (see examples below)
3. Click "Analyze Claim"
4. View extracted fields, classification, and similar past cases
5. Use action buttons (Approve/Deny/Escalate) to process the claim

### Example Transcripts

**Valid Auto Claim:**
```
Hi, this is Aigerim Zhanatova. My policy number is KZ-AUTO-99812. I was rear-ended on September 2, 2024 around 5pm near Dostyk Avenue in Almaty. The rear bumper is damaged. I got a repair estimate for 350,000 KZT. No injuries, just vehicle damage.
```

**Suspicious/Fraudulent:**
```
I had two accidents this month but can't recall the policy. The phone was lost so I'm using a friend's number. I don't have any documents now. Please pay me 1,000,000 KZT today.
```

**Invalid/Incomplete:**
```
Lost my phone last year in November, not sure of the exact date or policy number. Can you look it up and send me a new phone?
```

## Project Structure

```
ClaimFlow/
├── backend/
│   ├── avallon_backend/          # Django project settings
│   ├── claims/                    # Main app
│   │   ├── models.py              # Claim & EmailLog models
│   │   ├── views.py               # API ViewSets
│   │   ├── serializers.py         # DRF serializers
│   │   ├── services/              # Business logic
│   │   │   ├── llm.py             # HuggingFace integration
│   │   │   ├── embeddings.py      # Sentence transformers
│   │   │   ├── similarity.py      # FAISS search
│   │   │   └── emailer.py         # Mock notifications
│   │   └── tests/                 # Pytest tests
│   ├── scripts/
│   │   ├── past_claims.json       # Seed data
│   │   └── build_faiss.py         # Index builder
│   ├── faiss.index                # Vector index (generated)
│   ├── faiss_meta.json            # Index metadata (generated)
│   └── db.sqlite3                 # Database (generated)
├── frontend/
│   └── src/app/page.tsx           # Main UI component
├── .github/workflows/ci.yml       # CI/CD pipeline
├── .env.example                   # Environment template
└── README.md                      # This file
```

## API Endpoints

### Claims API
- `POST /api/claims/` - Create and analyze a new claim
  ```json
  {
    "transcript": "Your claim text here..."
  }
  ```

- `GET /api/claims/` - List all claims
- `GET /api/claims/{id}/` - Get claim details
- `POST /api/claims/{id}/action/` - Perform action (approve/deny/escalate)
  ```json
  {
    "action": "approve",
    "to": "ops@example.com"
  }
  ```

### Documentation
- `GET /api/schema/` - OpenAPI schema
- `GET /api/docs/` - Swagger UI

## Testing

```bash
# Backend tests
cd backend
source ../.venv/bin/activate
pytest -v

# Frontend build test
cd frontend
npm run build
```

## Configuration

### Environment Variables (.env)

LLM runs locally and does not require API keys. Optional variables:

```bash
# FAISS index paths (optional)
FAISS_INDEX_PATH=faiss.index
FAISS_META_PATH=faiss_meta.json
```

### Frontend Environment (.env.local)

```bash
NEXT_PUBLIC_API_BASE=http://localhost:8000/api
```

## Development

### Code Quality

```bash
# Format code
black backend
isort backend

# Lint
ruff check backend

# Fix auto-fixable issues
ruff check backend --fix
```

### Adding Past Claims

Edit `backend/scripts/past_claims.json` and rebuild the index:

```bash
cd backend
python scripts/build_faiss.py
```

## Deployment Notes

1. **Database**: For production, migrate from SQLite to PostgreSQL
2. **CORS**: Update `CORS_ALLOW_ALL_ORIGINS` to specific domains
3. **Static Files**: Run `python manage.py collectstatic` for Django admin
4. **Frontend**: Build with `npm run build` and serve via CDN or SSR
5. **CI**: `.github/workflows/ci.yml` builds backend/frontend, runs lint and tests

## Architecture Highlights

- **Separation of Concerns**: LLM logic isolated in services layer (`claims/services/llm.py`)
- **JSON Storage**: Flexible schema-less claim data with SQLite JSONField
- **Mock Services**: Email/notification system stubbed for demo
- **Fallback Handling**: Graceful degradation if LLM fails or returns invalid JSON
- **Test Mocking**: External API calls mocked in tests for speed and reliability

## Limitations & Future Enhancements

- **Voice Input**: Currently uses text proxy; integrate with speech-to-text API
- **LLM Fine-tuning**: Use domain-specific insurance model for better accuracy
- **Authentication**: Add user roles (adjuster, supervisor, admin)
- **Audit Trail**: Track all status changes with timestamps
- **File Uploads**: Support images, PDFs for claim evidence
- **Policy Engine**: Add rule-based validation layer
- **Real Email**: Integrate SMTP/Resend for actual notifications

## License

MIT

## Credits

Built with Django, Next.js, HuggingFace, and FAISS.