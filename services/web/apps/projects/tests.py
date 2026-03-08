import json
from uuid import uuid4

from apps.projects.models import Project, ProjectSourceType, ProjectStatus
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse


def test_project_defaults():
    project = Project(title="Data platform")

    assert project.status == ProjectStatus.DRAFT
    assert project.source_type == ProjectSourceType.MANUAL
    assert project.tech_tags == []


def _make_user():
    username = f"owner-{uuid4().hex[:8]}"
    return get_user_model().objects.create_user(username=username, password="test-pass-123")


def _title(prefix: str) -> str:
    return f"{prefix} {uuid4().hex[:8]}"


def test_create_project_defaults_extra_data_when_missing():
    user = _make_user()
    client = Client()
    client.force_login(user)

    response = client.post(
        reverse("api-v1-project-list"),
        data=json.dumps({"title": _title("Project without extra data")}),
        content_type="application/json",
    )

    assert response.status_code == 201
    project = Project.objects.get(pk=response.json()["pk"])
    assert project.extra_data == {}
    assert response.json()["extra_data"] == {}


def test_create_project_normalizes_null_extra_data():
    user = _make_user()
    client = Client()
    client.force_login(user)

    response = client.post(
        reverse("api-v1-project-list"),
        data=json.dumps({"title": _title("Project with null extra data"), "extra_data": None}),
        content_type="application/json",
    )

    assert response.status_code == 201
    project = Project.objects.get(pk=response.json()["pk"])
    assert project.extra_data == {}
    assert response.json()["extra_data"] == {}


def test_create_project_normalizes_null_tech_tags():
    user = _make_user()
    client = Client()
    client.force_login(user)

    response = client.post(
        reverse("api-v1-project-list"),
        data=json.dumps({"title": _title("Project with null tech tags"), "tech_tags": None}),
        content_type="application/json",
    )

    assert response.status_code == 201
    project = Project.objects.get(pk=response.json()["pk"])
    assert project.tech_tags == {}
    assert response.json()["tech_tags"] == {}
