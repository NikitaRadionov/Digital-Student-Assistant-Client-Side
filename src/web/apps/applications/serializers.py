from apps.base.serializers import UserPublicSerializer
from apps.projects.serializers import PrimaryProjectSerializer
from rest_framework import serializers

from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    project_snapshot = PrimaryProjectSerializer(source="project", read_only=True)
    applicant_snapshot = UserPublicSerializer(source="applicant", read_only=True)
    reviewed_by_snapshot = UserPublicSerializer(source="reviewed_by", read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "project",
            "project_snapshot",
            "applicant",
            "applicant_snapshot",
            "status",
            "motivation",
            "review_comment",
            "reviewed_by",
            "reviewed_by_snapshot",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "applicant",
            "review_comment",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        if instance is not None and "status" in attrs and attrs["status"] != instance.status:
            raise serializers.ValidationError(
                {"status": ["Direct status updates are disabled. Use transition action endpoints."]}
            )
        # Prevent duplicate application: check uniqueness before hitting the DB constraint
        if instance is None:
            request = self.context.get("request")
            project = attrs.get("project")
            if request and request.user.is_authenticated and project is not None:
                if Application.objects.filter(applicant=request.user, project=project).exists():
                    raise serializers.ValidationError(
                        {"project": ["You have already submitted an application for this project."]}
                    )
        return attrs
