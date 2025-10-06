import pytest
from rest_framework.test import APIClient
from claims.models import Claim, EmailLog


@pytest.mark.django_db
def test_create_claim(monkeypatch):
    """Test creating a claim with mocked LLM services"""
    client = APIClient()

    def mock_extract(t):
        return {
            "claimant_name": "John Smith",
            "policy_number": "TEST-123",
            "incident_description": "Test accident",
        }

    def mock_classify(e, t):
        return {
            "label": "valid",
            "score": 0.9,
            "rationale": "Test rationale",
            "policy_flags": [],
            "suggested_next_steps": ["request_documents"],
        }

    def mock_similar(t, k=3):
        return [{"id": "c1", "similarity": 0.82, "label": "valid"}]

    monkeypatch.setattr("claims.views.extract_entities", mock_extract)
    monkeypatch.setattr("claims.views.classify_claim", mock_classify)
    monkeypatch.setattr("claims.views.query_similar", mock_similar)

    # Make API request
    res = client.post(
        "/api/claims/",
        {"transcript": "John Smith had an accident..."},
        format="json",
    )

    assert res.status_code == 201
    data = res.json()
    assert data["extracted"]["claimant_name"] == "John Smith"
    assert data["classification"]["label"] == "valid"
    assert data["suggestions"]["next_steps"] == ["request_documents"]
    assert data["status"] == "analysed"
    assert len(data["similar"]) == 1


@pytest.mark.django_db
def test_claim_action():
    """Test performing actions on a claim"""
    client = APIClient()

    # Create a test claim directly
    claim = Claim.objects.create(
        transcript="Test transcript",
        extracted={"claimant_name": "Jane Doe"},
        classification={"label": "valid", "score": 0.95},
        status="analysed",
    )

    # Test approve action
    res = client.post(
        f"/api/claims/{claim.id}/action/",
        {"action": "approve", "to": "test@example.com"},
        format="json",
    )

    assert res.status_code == 200
    claim.refresh_from_db()
    assert claim.status == "approved"

    # Verify email log was created
    assert EmailLog.objects.filter(claim=claim).count() == 1
    email = EmailLog.objects.get(claim=claim)
    assert email.to == "test@example.com"
    assert "approve" in email.subject.lower()


@pytest.mark.django_db
def test_list_claims():
    """Test listing claims"""
    client = APIClient()

    # Create test claims
    Claim.objects.create(
        transcript="Test 1", extracted={}, classification={}, status="received"
    )
    Claim.objects.create(
        transcript="Test 2", extracted={}, classification={}, status="analysed"
    )

    res = client.get("/api/claims/")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
