from apps.applications.models import Application
from apps.frontend.forms import ProfileEditForm
from apps.frontend.utils import LOGIN_URL
from apps.projects.models import Project, ProjectSourceType, ProjectStatus
from apps.projects.normalization import normalize_technology_tags
from apps.users.models import UserRole
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def _parse_interests(raw: str) -> list[str]:
    return normalize_technology_tags(raw.split(",")) if raw.strip() else []


@login_required(login_url=LOGIN_URL)
def profile_view(request):
    user = request.user
    try:
        profile = user.profile
        role    = profile.role
    except AttributeError:
        profile = None
        role    = ""

    if request.method == "POST":
        form = ProfileEditForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data["full_name"]
            bio       = form.cleaned_data["bio"]
            interests = form.cleaned_data["interests_raw"]

            parts = full_name.split(None, 1)
            user.first_name = parts[0] if parts else ""
            user.last_name  = parts[1] if len(parts) > 1 else ""
            user.save(update_fields=["first_name", "last_name"])

            if profile:
                profile.bio       = bio
                profile.interests = interests
                profile.save(update_fields=["bio", "interests"])

            messages.success(request, "Профиль обновлён.")
            return redirect("frontend:profile")
    else:
        interests_str = ",".join(profile.interests) if profile and profile.interests else ""
        form = ProfileEditForm(initial={
            "full_name":     f"{user.first_name} {user.last_name}".strip(),
            "bio":           profile.bio if profile else "",
            "interests_raw": interests_str,
        })

    own_projects_count = (
        Project.objects.filter(owner=user).count()
        if role == UserRole.CUSTOMER else 0
    )

    applications_count = 0
    bookmarks_count    = 0
    initiative_count   = 0
    if role == UserRole.STUDENT:
        applications_count = Application.objects.filter(applicant=user).count()
        bookmarks_count    = len(profile.favorite_project_ids) if profile else 0
        initiative_count   = Project.objects.filter(
            owner=user, source_type=ProjectSourceType.INITIATIVE
        ).count()

    moderation_queue_count = (
        Project.objects.filter(status=ProjectStatus.ON_MODERATION).count()
        if role == UserRole.CPPRP else 0
    )

    return render(request, "frontend/profile.html", {
        "profile_user":           user,
        "profile":                profile,
        "role":                   role,
        "form":                   form,
        "own_projects_count":     own_projects_count,
        "applications_count":     applications_count,
        "bookmarks_count":        bookmarks_count,
        "initiative_count":       initiative_count,
        "moderation_queue_count": moderation_queue_count,
    })
