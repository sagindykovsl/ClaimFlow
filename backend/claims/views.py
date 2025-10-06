from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import ClaimCreateSerializer, ClaimSerializer, EmailLogSerializer
from .models import Claim, EmailLog
from .services.llm import extract_entities, classify_claim
from .services.similarity import query_similar


class ClaimViewSet(viewsets.ModelViewSet):
    queryset = Claim.objects.all().order_by("-created_at")
    serializer_class = ClaimSerializer

    def create(self, request, *args, **kwargs):
        """Create a new claim from transcript and analyze it"""
        ser = ClaimCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        transcript = ser.validated_data["transcript"]

        # Extract entities from transcript
        extracted = extract_entities(transcript)

        # Classify the claim
        classification = classify_claim(extracted, transcript)

        # Find similar past claims
        similar = query_similar(transcript, k=3)

        # Create claim record
        claim = Claim.objects.create(
            transcript=transcript,
            extracted=extracted,
            classification=classification,
            suggestions={"next_steps": classification.get("suggested_next_steps", [])},
            status="analysed",
            similar=similar,
        )
        return Response(ClaimSerializer(claim).data, status=201)

    @action(detail=True, methods=["post"])
    def action(self, request, pk=None):
        """Perform action on a claim (approve/deny/escalate)"""
        claim = self.get_object()
        action_type = request.data.get("action")
        
        if action_type not in ("approve", "deny", "escalate"):
            return Response({"detail": "Invalid action"}, status=400)
        
        email_to = request.data.get("to", "ops@example.com")
        subject = f"Claim {claim.id} {action_type}"
        body = f"Automated action for claim {claim.id}: {action_type}\n\nExtracted: {claim.extracted}"

        # Create email log
        log = EmailLog.objects.create(
            claim=claim, to=email_to, subject=subject, body=body, meta={"action": action_type}
        )

        # Update claim status
        if action_type == "approve":
            claim.status = "approved"
        elif action_type == "deny":
            claim.status = "denied"
        else:
            claim.status = "escalated"
        claim.save()

        return Response(EmailLogSerializer(log).data, status=200)
