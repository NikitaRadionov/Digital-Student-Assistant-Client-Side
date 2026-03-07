from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Project, ProjectStatus
from .serializers import PrimaryProjectSerializer


class ProjectListCreateAPIView(generics.ListCreateAPIView):
    queryset = Project.objects.select_related("owner")
    serializer_class = PrimaryProjectSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return self.queryset.filter(
                Q(status=ProjectStatus.PUBLISHED) | Q(owner=user)
            ).distinct()
        return self.queryset.filter(status=ProjectStatus.PUBLISHED)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


project_list_create_view = ProjectListCreateAPIView.as_view()


class ProjectDetailAPIView(generics.RetrieveAPIView):
    queryset = Project.objects.select_related("owner")
    serializer_class = PrimaryProjectSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return self.queryset.filter(
                Q(status=ProjectStatus.PUBLISHED) | Q(owner=user)
            ).distinct()
        return self.queryset.filter(status=ProjectStatus.PUBLISHED)


project_detail_view = ProjectDetailAPIView.as_view()


class ProjectUpdateAPIView(generics.UpdateAPIView):
    queryset = Project.objects.select_related("owner")
    serializer_class = PrimaryProjectSerializer
    lookup_field = "pk"

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(owner=user)


project_update_view = ProjectUpdateAPIView.as_view()


class ProjectDestroyAPIView(generics.DestroyAPIView):
    queryset = Project.objects.select_related("owner")
    serializer_class = PrimaryProjectSerializer
    lookup_field = "pk"

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(owner=user)


project_destroy_view = ProjectDestroyAPIView.as_view()


class ProjectRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.select_related("owner")
    serializer_class = PrimaryProjectSerializer
    lookup_field = "pk"

    def get_queryset(self):
        user = self.request.user
        if self.request.method in {"GET", "HEAD", "OPTIONS"}:
            if user.is_authenticated:
                return self.queryset.filter(
                    Q(status=ProjectStatus.PUBLISHED) | Q(owner=user)
                ).distinct()
            return self.queryset.filter(status=ProjectStatus.PUBLISHED)

        if user.is_staff:
            return self.queryset
        return self.queryset.filter(owner=user)


project_rud_view = ProjectRetrieveUpdateDestroyAPIView.as_view()


class CreateAPIView(mixins.CreateModelMixin, generics.GenericAPIView):
    pass


class ProjectMixinView(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    generics.GenericAPIView,
):
    queryset = Project.objects.select_related("owner")
    serializer_class = PrimaryProjectSerializer
    lookup_field = "pk"

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return self.queryset.filter(
                Q(status=ProjectStatus.PUBLISHED) | Q(owner=user)
            ).distinct()
        return self.queryset.filter(status=ProjectStatus.PUBLISHED)

    def get(self, request, *args, **kwargs):
        if kwargs.get("pk") is not None:
            return self.retrieve(request, *args, **kwargs)
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


project_mixin_view = ProjectMixinView.as_view()


@api_view(["GET", "POST"])
def project_alt_view(request, pk=None, *args, **kwargs):
    if request.method == "GET":
        if pk is not None:
            obj = get_object_or_404(Project, pk=pk)
            return Response(PrimaryProjectSerializer(obj, many=False).data)

        queryset = Project.objects.filter(status=ProjectStatus.PUBLISHED)
        if request.user.is_authenticated:
            queryset = Project.objects.filter(
                Q(status=ProjectStatus.PUBLISHED) | Q(owner=request.user)
            ).distinct()
        return Response(PrimaryProjectSerializer(queryset, many=True).data)

    serializer = PrimaryProjectSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(owner=request.user)
    return Response({"data": serializer.data})
