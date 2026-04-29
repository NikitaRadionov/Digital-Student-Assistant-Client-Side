"""
Technologies directory view.

Shows all approved technologies with project counts; CPPRP staff can also
approve or reject pending technologies from this page.
"""

import logging

from apps.frontend.decorators import moderator_required
from apps.projects.models import Project, ProjectStatus, Technology, TechnologyStatus
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

# Statuses that count as "live" projects for the per-technology counter
_LIVE_STATUSES = [ProjectStatus.PUBLISHED, ProjectStatus.STAFFED]


def _is_moderator(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    try:
        from apps.users.utils import user_is_moderator
        return user_is_moderator(user)
    except Exception:
        return False


@login_required(login_url="/auth/")
def technology_list(request):
    """Technology directory: all approved techs, sorted by live-project count."""
    live_filter = Q(projects__status__in=_LIVE_STATUSES)

    approved_qs = (
        Technology.objects.approved()
        .annotate(
            project_count=Count("projects", filter=live_filter, distinct=True)
        )
        .order_by("-project_count", "normalized_name")
    )

    pending_list = []
    is_mod = _is_moderator(request.user)
    if is_mod:
        pending_list = list(
            Technology.objects.filter(status=TechnologyStatus.PENDING)
            .annotate(
                project_count=Count("projects", filter=live_filter, distinct=True)
            )
            .order_by("-project_count", "normalized_name")
        )

    context = {
        "approved_technologies": approved_qs,
        "pending_technologies": pending_list,
        "is_moderator": is_mod,
        "total_approved": approved_qs.count(),
    }
    return render(request, "frontend/technology_list.html", context)


@require_POST
@login_required(login_url="/auth/")
@moderator_required
def technology_moderate(request, pk):
    """CPPRP approves or rejects a pending technology."""
    tech = get_object_or_404(Technology, pk=pk, status=TechnologyStatus.PENDING)
    action = request.POST.get("action", "").strip()

    if action == "approve":
        tech.status = TechnologyStatus.APPROVED
        tech.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Технология «{tech.name}» одобрена.")
    elif action == "reject":
        tech.status = TechnologyStatus.REJECTED
        tech.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Технология «{tech.name}» отклонена.")
    else:
        messages.error(request, "Неизвестное действие.")

    return redirect("frontend:technology_list")
