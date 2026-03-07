from rest_framework import serializers

from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = [
            "id",
            "project",
            "applicant",
            "status",
            "motivation",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "applicant", "created_at", "updated_at"]
