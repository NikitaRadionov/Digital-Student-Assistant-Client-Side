import csv

from apps.account.models import DeadlineAudience, DocumentTemplate, PlatformDeadline
from apps.applications.models import Application, ApplicationStatus
from apps.frontend.decorators import moderator_required
from apps.frontend.forms import DeadlineForm, ExternalAllowlistBulkForm, TemplateForm
from apps.frontend.utils import flash_form_errors
from apps.projects.models import Project, ProjectStatus
from apps.users.models import (
    ExternalAccessAllowlist,
    ExternalAccessRequest,
    ExternalAccessRequestStatus,
    UserProfile,
    UserRole,
)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST

_LOGIN_URL      = reverse_lazy("frontend:auth")
_APPS_PAGE_SIZE = 20


def _cpprp_tab_redirect(tab: str) -> HttpResponse:
    return redirect(reverse("frontend:cpprp_dashboard") + f"?tab={tab}")


@login_required(login_url=_LOGIN_URL)
@moderator_required
def cpprp_dashboard(request):
    project_counts = Project.objects.aggregate(
        **{s: Count("pk", filter=Q(status=s)) for s in [
            ProjectStatus.PUBLISHED,
            ProjectStatus.ON_MODERATION,
            ProjectStatus.STAFFED,
            ProjectStatus.DRAFT,
        ]}
    )

    app_totals = Application.objects.aggregate(
        submitted=Count("pk", filter=Q(status=ApplicationStatus.SUBMITTED)),
        accepted=Count("pk",  filter=Q(status=ApplicationStatus.ACCEPTED)),
        rejected=Count("pk",  filter=Q(status=ApplicationStatus.REJECTED)),
    )
    app_totals["total"] = sum(app_totals.values())

    active_students_count = (
        Application.objects
        .filter(status=ApplicationStatus.ACCEPTED)
        .values("applicant_id")
        .distinct()
        .count()
    )
    total_students_count = UserProfile.objects.filter(role=UserRole.STUDENT).count()

    app_status_filter = request.GET.get("status", "").strip()
    app_page          = request.GET.get("page", 1)

    apps_qs = (
        Application.objects
        .select_related("applicant", "project")
        .order_by("-created_at")
    )
    if app_status_filter and app_status_filter in ApplicationStatus.values:
        apps_qs = apps_qs.filter(status=app_status_filter)

    apps_paginator = Paginator(apps_qs, _APPS_PAGE_SIZE)
    apps_page_obj  = apps_paginator.get_page(app_page)

    deadlines = list(PlatformDeadline.objects.order_by("ends_at", "title"))
    templates = list(DocumentTemplate.objects.order_by("title"))
    external_pending_requests = list(
        ExternalAccessRequest.objects.filter(status=ExternalAccessRequestStatus.PENDING)
        .order_by("created_at")
    )
    external_recent_requests = list(
        ExternalAccessRequest.objects.select_related("reviewed_by").order_by("-updated_at")[:20]
    )
    external_allowlist = list(
        ExternalAccessAllowlist.objects.select_related("approved_by").order_by("email")[:50]
    )

    return render(request, "frontend/cpprp_dashboard.html", {
        "project_counts":        project_counts,
        "app_totals":            app_totals,
        "active_students_count": active_students_count,
        "total_students_count":  total_students_count,
        "apps_page_obj":         apps_page_obj,
        "app_status_filter":     app_status_filter,
        "deadlines":             deadlines,
        "deadline_form":         DeadlineForm(),
        "templates":             templates,
        "template_form":         TemplateForm(),
        "external_pending_requests": external_pending_requests,
        "external_recent_requests": external_recent_requests,
        "external_allowlist": external_allowlist,
        "external_allowlist_form": ExternalAllowlistBulkForm(),
        "ApplicationStatus":     ApplicationStatus,
        "ProjectStatus":         ProjectStatus,
        "DeadlineAudience":      DeadlineAudience,
        "ExternalAccessRequestStatus": ExternalAccessRequestStatus,
    })


@require_POST
@login_required(login_url=_LOGIN_URL)
@moderator_required
def cpprp_deadline_create(request):
    form = DeadlineForm(request.POST)
    if form.is_valid():
        d = form.cleaned_data
        try:
            with transaction.atomic():
                PlatformDeadline.objects.create(
                    slug=d["slug"],
                    title=d["title"],
                    audience=d["audience"],
                    description=d.get("description", ""),
                    starts_at=d.get("starts_at"),
                    ends_at=d.get("ends_at"),
                    is_active=d.get("is_active", True),
                )
            messages.success(request, f"Дедлайн «{d['title']}» создан.")
        except IntegrityError:
            messages.error(request, "Не удалось создать дедлайн — такой slug уже занят.")
    else:
        flash_form_errors(request, form)
    return _cpprp_tab_redirect("deadlines")


@require_POST
@login_required(login_url=_LOGIN_URL)
@moderator_required
def cpprp_deadline_toggle(request, pk):
    dl          = get_object_or_404(PlatformDeadline, pk=pk)
    dl.is_active = not dl.is_active
    dl.save(update_fields=["is_active", "updated_at"])
    state = "активирован" if dl.is_active else "деактивирован"
    messages.success(request, f"Дедлайн «{dl.title}» {state}.")
    return _cpprp_tab_redirect("deadlines")


@require_POST
@login_required(login_url=_LOGIN_URL)
@moderator_required
def cpprp_deadline_delete(request, pk):
    dl    = get_object_or_404(PlatformDeadline, pk=pk)
    title = dl.title
    dl.delete()
    messages.success(request, f"Дедлайн «{title}» удалён.")
    return _cpprp_tab_redirect("deadlines")


@require_POST
@login_required(login_url=_LOGIN_URL)
@moderator_required
def cpprp_template_create(request):
    form = TemplateForm(request.POST)
    if form.is_valid():
        d = form.cleaned_data
        try:
            with transaction.atomic():
                DocumentTemplate.objects.create(
                    slug=d["slug"],
                    title=d["title"],
                    url=d["url"],
                    audience=d["audience"],
                    description=d.get("description", ""),
                    is_active=d.get("is_active", True),
                )
            messages.success(request, f"Шаблон «{d['title']}» добавлен.")
        except IntegrityError:
            messages.error(request, "Не удалось добавить шаблон — такой slug уже занят.")
    else:
        flash_form_errors(request, form)
    return _cpprp_tab_redirect("templates")


@require_POST
@login_required(login_url=_LOGIN_URL)
@moderator_required
def cpprp_template_toggle(request, pk):
    tpl          = get_object_or_404(DocumentTemplate, pk=pk)
    tpl.is_active = not tpl.is_active
    tpl.save(update_fields=["is_active", "updated_at"])
    state = "активирован" if tpl.is_active else "деактивирован"
    messages.success(request, f"Шаблон «{tpl.title}» {state}.")
    return _cpprp_tab_redirect("templates")


@require_POST
@login_required(login_url=_LOGIN_URL)
@moderator_required
def cpprp_template_delete(request, pk):
    tpl   = get_object_or_404(DocumentTemplate, pk=pk)
    title = tpl.title
    tpl.delete()
    messages.success(request, f"Шаблон «{title}» удалён.")
    return _cpprp_tab_redirect("templates")


@login_required(login_url=_LOGIN_URL)
@moderator_required
def cpprp_export_projects(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="projects-export.csv"'
    response.write("﻿")

    writer = csv.writer(response)
    writer.writerow([
        "id", "title", "status", "source_type",
        "team_size", "accepted_participants_count",
        "education_program", "study_course", "created_at",
    ])
    for p in Project.objects.select_related("owner").order_by("pk"):
        writer.writerow([
            p.pk, p.title, p.status, p.source_type,
            p.team_size, p.accepted_participants_count,
            p.education_program, p.study_course,
            p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
        ])
    return response


@login_required(login_url=_LOGIN_URL)
@moderator_required
def cpprp_export_applications(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="applications-export.csv"'
    response.write("﻿")

    writer = csv.writer(response)
    writer.writerow([
        "id", "project_id", "project_title",
        "applicant_id", "applicant_email",
        "status", "created_at",
    ])
    for a in Application.objects.select_related("project", "applicant").order_by("pk"):
        writer.writerow([
            a.pk, a.project_id, a.project.title,
            a.applicant_id, a.applicant.email,
            a.status,
            a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "",
        ])
    return response


@require_POST
@login_required(login_url=_LOGIN_URL)
@moderator_required
def cpprp_external_allowlist_bulk_add(request):
    form = ExternalAllowlistBulkForm(request.POST)
    if not form.is_valid():
        flash_form_errors(request, form)
        return _cpprp_tab_redirect("external-access")

    cleaned = form.cleaned_data
    created_count = 0
    updated_count = 0
    for email in cleaned["emails"]:
        entry, created = ExternalAccessAllowlist.objects.get_or_create(
            email=email,
            defaults={
                "allowed_role": cleaned["allowed_role"],
                "note": cleaned.get("note", ""),
                "approved_by": request.user,
                "is_active": True,
            },
        )
        if created:
            created_count += 1
            continue
        entry.allowed_role = cleaned["allowed_role"]
        entry.note = cleaned.get("note", "")
        entry.approved_by = request.user
        entry.is_active = True
        entry.save(update_fields=["allowed_role", "note", "approved_by", "is_active", "updated_at"])
        updated_count += 1

    messages.success(
        request,
        f"External allowlist updated: created {created_count}, updated {updated_count}.",
    )
    return _cpprp_tab_redirect("external-access")


@require_POST
@login_required(login_url=_LOGIN_URL)
@moderator_required
def cpprp_external_request_approve(request, pk):
    access_request = get_object_or_404(ExternalAccessRequest, pk=pk)
    entry, _ = ExternalAccessAllowlist.objects.get_or_create(
        email=access_request.email,
        defaults={
            "allowed_role": access_request.requested_role,
            "approved_by": request.user,
            "note": "Approved from external access request.",
            "is_active": True,
        },
    )
    entry.allowed_role = access_request.requested_role
    entry.approved_by = request.user
    entry.is_active = True
    if not entry.note:
        entry.note = "Approved from external access request."
    entry.save(update_fields=["allowed_role", "approved_by", "is_active", "note", "updated_at"])

    access_request.status = ExternalAccessRequestStatus.APPROVED
    access_request.reviewed_by = request.user
    access_request.reviewed_at = timezone.now()
    access_request.decision_note = "Approved and added to allowlist."
    access_request.save(
        update_fields=["status", "reviewed_by", "reviewed_at", "decision_note", "updated_at"]
    )
    messages.success(request, f"{access_request.email} approved and added to allowlist.")
    return _cpprp_tab_redirect("external-access")


@require_POST
@login_required(login_url=_LOGIN_URL)
@moderator_required
def cpprp_external_request_reject(request, pk):
    access_request = get_object_or_404(ExternalAccessRequest, pk=pk)
    access_request.status = ExternalAccessRequestStatus.REJECTED
    access_request.reviewed_by = request.user
    access_request.reviewed_at = timezone.now()
    access_request.decision_note = "Rejected by moderator."
    access_request.save(
        update_fields=["status", "reviewed_by", "reviewed_at", "decision_note", "updated_at"]
    )
    messages.success(request, f"{access_request.email} rejected.")
    return _cpprp_tab_redirect("external-access")


@require_POST
@login_required(login_url=_LOGIN_URL)
@moderator_required
def cpprp_external_allowlist_toggle(request, pk):
    entry = get_object_or_404(ExternalAccessAllowlist, pk=pk)
    entry.is_active = not entry.is_active
    entry.approved_by = request.user
    entry.save(update_fields=["is_active", "approved_by", "updated_at"])
    state = "activated" if entry.is_active else "deactivated"
    messages.success(request, f"{entry.email} {state}.")
    return _cpprp_tab_redirect("external-access")
