from apps.account.permissions import IsCustomerOrStaff, IsStudentOrStaff
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Application
from .serializers import ApplicationSerializer
from .services import create_application, delete_application, review_application_service


class ApplicationListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ApplicationSerializer

    def get_permissions(self):
        return [IsStudentOrStaff()]

    def get_queryset(self):
        queryset = Application.objects.select_related("project", "applicant")
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(applicant=user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project    = serializer.validated_data["project"]
        motivation = serializer.validated_data.get("motivation", "")

        application, _ = create_application(
            project=project,
            applicant=request.user,
            motivation=motivation,
        )

        out     = ApplicationSerializer(application, context={"request": request})
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)


class ApplicationRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [IsStudentOrStaff]
    lookup_field = "pk"

    def get_queryset(self):
        queryset = Application.objects.select_related("project", "applicant")
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(applicant=user)

    def perform_destroy(self, instance):
        delete_application(instance)


class ApplicationReviewInputSerializer(drf_serializers.Serializer):
    decision = drf_serializers.ChoiceField(choices=["accept", "reject"])
    comment  = drf_serializers.CharField(required=False, allow_blank=True, default="")


class ApplicationReviewAPIView(APIView):
    permission_classes = [IsCustomerOrStaff]

    @extend_schema(
        request=ApplicationReviewInputSerializer,
        responses=ApplicationSerializer,
    )
    def post(self, request, pk: int):
        input_serializer = ApplicationReviewInputSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        application = generics.get_object_or_404(
            Application.objects.select_related("project", "project__owner", "applicant"),
            pk=pk,
        )
        review_application_service(
            application=application,
            actor=request.user,
            decision=input_serializer.validated_data["decision"],
            comment=input_serializer.validated_data["comment"],
        )

        serializer = ApplicationSerializer(application, context={"request": request})
        return Response(serializer.data)
