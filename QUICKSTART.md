# ClaimFlow - Quick Start Guide

## Initial Setup (One-time)

### 1. Get HuggingFace Token

1. Visit https://huggingface.co/settings/tokens
2. Create a free account if needed
3. Generate a new token (read access is sufficient)
4. Copy the token (starts with `hf_...`)

### 2. Configure Environment

```bash
# Create .env file in root directory
cp .env.example .env

# Edit .env and add your token:
# HF_TOKEN=hf_your_actual_token_here
```

### 3. Backend Setup

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all backend dependencies
pip install django djangorestframework django-cors-headers drf-spectacular \
            pydantic python-dotenv requests sentence-transformers faiss-cpu \
            black isort ruff pytest pytest-django

# Navigate to backend directory
cd backend

# Run database migrations
python manage.py migrate

# Build FAISS similarity index (downloads ~100MB model first time)
python scripts/build_faiss.py
```

### 4. Frontend Setup

```bash
# In a new terminal, from project root
cd frontend

# Install dependencies
npm install
```

## Running the Application

You need **two terminal windows**:

### Terminal 1 - Backend Server

```bash
cd backend
source ../.venv/bin/activate
python manage.py runserver 8000
```

**Backend will be ready when you see:**
```
Starting development server at http://127.0.0.1:8000/
```

**Available at:**
- API: http://localhost:8000/api/claims/
- Swagger Docs: http://localhost:8000/api/docs/

### Terminal 2 - Frontend Server

```bash
cd frontend
npm run dev
```

**Frontend will be ready when you see:**
```
Local: http://localhost:3000
```

**Open in browser:** http://localhost:3000

## Testing the Application

### Sample Claim Transcripts

Copy and paste into the UI:

**1. Valid Auto Claim**
```
Hi, this is Aigerim Zhanatova. My policy number is KZ-AUTO-99812. I was rear-ended on September 2, 2024 around 5pm near Dostyk Avenue in Almaty. The rear bumper is damaged. I got a repair estimate for 350,000 KZT. No injuries, just vehicle damage.
```

**2. Fraudulent Claim (Suspicious)**
```
I had two accidents this month but can't recall the policy. The phone was lost so I'm using a friend's number. I don't have any documents now. Please pay me 1,000,000 KZT today.
```

**3. Invalid/Incomplete Claim**
```
Lost my phone last year in November, not sure of the exact date or policy number. Can you look it up and send me a new phone?
```

### Expected Results

After clicking "Analyze Claim", you should see:

1. **Extracted Fields** - JSON with claimant name, policy number, amounts, etc.
2. **Classification** - Label (valid/invalid/fraudulent), confidence score, rationale
3. **Similar Past Cases** - Up to 3 similar claims from the database with similarity scores
4. **Action Buttons** - Approve, Deny, or Escalate

### Running Tests

```bash
# Backend tests
cd backend
source ../.venv/bin/activate
pytest -v

# All tests should pass:
# ✓ test_create_claim
# ✓ test_claim_action  
# ✓ test_list_claims
```

## Troubleshooting

### Backend Issues

**"No module named 'django'"**
- Activate virtual environment: `source .venv/bin/activate`

**"HF_TOKEN not found"**
- Check .env file exists in backend directory
- Verify HF_TOKEN=hf_... is present

**"FAISS index not found"**
- Run: `python scripts/build_faiss.py`

**First FAISS build slow (5-10 min)**
- Downloads sentence-transformers model (~100MB)
- Only happens once, subsequent runs are fast

### Frontend Issues

**"ECONNREFUSED localhost:8000"**
- Make sure backend server is running first
- Check backend terminal for errors

**Port 3000 in use**
- Kill existing process or use different port:
  `PORT=3001 npm run dev`

### LLM Issues

**"Rate limit exceeded"**
- HuggingFace free tier has rate limits
- Wait 1-2 minutes between requests
- Consider upgrading to Pro tier

**JSON parsing errors in console**
- LLM sometimes returns markdown-wrapped JSON
- Code includes fallback parsing logic
- Try simpler transcript if issues persist

## Next Steps

1. **Explore API Docs**: http://localhost:8000/api/docs/
2. **View Admin Panel**: 
   - Create superuser: `python manage.py createsuperuser`
   - Visit: http://localhost:8000/admin/
3. **Add More Past Claims**: Edit `backend/scripts/past_claims.json` and rebuild index
4. **Customize UI**: Edit `frontend/src/app/page.tsx`
5. **Review Code Quality**: Run `black`, `isort`, `ruff` in backend

## Stopping Servers

- Press `Ctrl+C` in each terminal window
- Deactivate Python venv: `deactivate`

## Clean Restart

```bash
# Stop all servers (Ctrl+C)

# Backend
cd backend
source ../.venv/bin/activate
python manage.py migrate  # Reapply migrations if needed
python manage.py runserver 8000

# Frontend (new terminal)
cd frontend
npm run dev
```

## Getting Help

- Check `README.md` for detailed documentation
- Review Django logs in backend terminal
- Check browser console (F12) for frontend errors
- Verify .env file configuration
