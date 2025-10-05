from rest_framework import serializers
from .models import Claim, EmailLog


class ClaimCreateSerializer(serializers.Serializer):
    transcript = serializers.CharField(max_length=10000)


class ClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = Claim
        fields = "__all__"


class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = "__all__"
