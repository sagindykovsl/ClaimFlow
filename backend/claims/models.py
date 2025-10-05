from django.db import models


class Claim(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # raw user input (transcript proxy for voice)
    transcript = models.TextField()

    # extracted fields (as JSON)
    extracted = models.JSONField(default=dict, blank=True)

    # classification: label + score + rationale
    classification = models.JSONField(default=dict, blank=True)

    # suggested next steps (LLM output)
    suggestions = models.JSONField(default=dict, blank=True)

    # status lifecycle
    status = models.CharField(
        max_length=24,
        choices=[
            ("received", "received"),
            ("analysed", "analysed"),
            ("approved", "approved"),
            ("denied", "denied"),
            ("escalated", "escalated"),
        ],
        default="received",
    )

    # similarity matches (top-k)
    similar = models.JSONField(default=list, blank=True)

    def __str__(self):
        return f"Claim {self.id} - {self.status}"

    class Meta:
        ordering = ["-created_at"]


class EmailLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    claim = models.ForeignKey(Claim, on_delete=models.CASCADE, related_name="emails")
    to = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    meta = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Email to {self.to} for Claim {self.claim_id}"

    class Meta:
        ordering = ["-created_at"]
