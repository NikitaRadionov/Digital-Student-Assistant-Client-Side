from types import SimpleNamespace
from uuid import uuid4

import pytest
from apps.applications.admin import ApplicationAdmin
from apps.applications.models import Application, ApplicationStatus
from apps.projects.models import Project, ProjectSourceType, ProjectStatus
from django.contrib import admin
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _application_admin() -> ApplicationAdmin:
    return admin.site._registry[Application]


def _uid() -> str:
    return uuid4().hex[:8]


def test_application_registered_in_admin():
    assert Application in admin.site._registry
    assert isinstance(_application_admin(), ApplicationAdmin)


def test_application_admin_export_action_registered():
    assert "export_selected_as_csv" in _application_admin().actions


def test_application_admin_export_action_returns_csv():
    owner = User.objects.create_user(
        username=f"application-admin-owner-{_uid()}",
        email=f"owner-{_uid()}@app.test",
    )
    applicant = User.objects.create_user(
        username=f"application-admin-applicant-{_uid()}",
        email=f"applicant-{_uid()}@app.test",
    )
    project = Project.objects.create(
        title="Application export project",
        description="Admin export test",
        owner=owner,
        status=ProjectStatus.PUBLISHED,
        source_type=ProjectSourceType.MANUAL,
    )
    application = Application.objects.create(
        project=project,
        applicant=applicant,
        status=ApplicationStatus.SUBMITTED,
        motivation="Test motivation",
    )
    request = RequestFactory().get("/admin/applications/application/")

    response = _application_admin().export_selected_as_csv(
        request,
        Application.objects.filter(pk=application.pk),
    )

    content = response.content.decode("utf-8-sig")
    assert response.status_code == 200
    assert response["Content-Disposition"] == 'attachment; filename="applications-export.csv"'
    assert "id,project_id,project_title,applicant_id,applicant_email,status,created_at" in content
    assert (
        f"{application.pk},{project.pk},Application export project,"
        f"{applicant.pk},{applicant.email},submitted,"
    ) in content


def test_application_admin_export_all_view_returns_csv():
    owner = User.objects.create_user(
        username=f"application-admin-owner-all-{_uid()}",
        email=f"owner-all-{_uid()}@app.test",
    )
    applicant = User.objects.create_user(
        username=f"application-admin-applicant-all-{_uid()}",
        email=f"applicant-all-{_uid()}@app.test",
    )
    project = Project.objects.create(
        title="Application export all project",
        description="Admin export all test",
        owner=owner,
        status=ProjectStatus.PUBLISHED,
        source_type=ProjectSourceType.MANUAL,
    )
    application = Application.objects.create(
        project=project,
        applicant=applicant,
        status=ApplicationStatus.SUBMITTED,
    )
    request = RequestFactory().get(reverse("admin:applications_application_export_all"))
    request.user = SimpleNamespace(is_active=True, is_staff=True)

    response = _application_admin().export_all_as_csv_view(request)

    content = response.content.decode("utf-8-sig")
    assert response.status_code == 200
    assert f"{application.pk},{project.pk},Application export all project," in content
