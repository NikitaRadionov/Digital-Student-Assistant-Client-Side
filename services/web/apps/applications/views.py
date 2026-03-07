from rest_framework import generics, permissions

from .models import Application
from .serializers import ApplicationSerializer


class ApplicationListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Application.objects.select_related("project", "applicant")
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(applicant=user)

    def perform_create(self, serializer):
        serializer.save(applicant=self.request.user)


class ApplicationRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "pk"

    def get_queryset(self):
        queryset = Application.objects.select_related("project", "applicant")
        user = self.request.user
        if user.is_staff:
            return queryset
        return queryset.filter(applicant=user)
