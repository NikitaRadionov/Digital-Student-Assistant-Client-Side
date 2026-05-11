from apps.account.models import DeadlineAudience, DocumentTemplate, PlatformDeadline
from apps.applications.models import Application, ApplicationStatus
from apps.frontend.decorators import student_required
from apps.projects.models import Project, ProjectStatus
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render
from django.urls import reverse_lazy

_LOGIN_URL      = reverse_lazy("frontend:auth")
_RECENT_APPS    = 5
_RECENT_FAVS    = 6


@login_required(login_url=_LOGIN_URL)
@student_required
def student_overview(request):
    user = request.user

    all_apps = (
        Application.objects
        .filter(applicant=user)
        .select_related("project")
        .order_by("-created_at")
    )
    counters = all_apps.aggregate(
        total=Count("pk"),
        submitted=Count("pk", filter=Q(status=ApplicationStatus.SUBMITTED)),
        accepted=Count("pk",  filter=Q(status=ApplicationStatus.ACCEPTED)),
        rejected=Count("pk",  filter=Q(status=ApplicationStatus.REJECTED)),
    )
    recent_apps = list(all_apps[:_RECENT_APPS])

    try:
        fav_ids = list(user.profile.favorite_project_ids or [])
    except AttributeError:
        fav_ids = []

    counters["favorites"] = len(fav_ids)
    fav_projects = (
        list(
            Project.objects
            .filter(pk__in=fav_ids[:_RECENT_FAVS])
            .select_related("owner")
            .order_by("-updated_at")
        )
        if fav_ids else []
    )

    deadlines = list(
        PlatformDeadline.objects.filter(
            is_active=True,
            audience__in=[DeadlineAudience.GLOBAL, DeadlineAudience.STUDENT],
        ).order_by("ends_at", "title")
    )
    templates = list(
        DocumentTemplate.objects.filter(
            is_active=True,
            audience__in=[DeadlineAudience.GLOBAL, DeadlineAudience.STUDENT],
        ).order_by("title")
    )

    return render(request, "frontend/student_overview.html", {
        "counters":       counters,
        "recent_apps":    recent_apps,
        "fav_projects":   fav_projects,
        "fav_ids_total":  len(fav_ids),
        "deadlines":      deadlines,
        "templates":      templates,
        "ApplicationStatus": ApplicationStatus,
        "ProjectStatus":     ProjectStatus,
    })
