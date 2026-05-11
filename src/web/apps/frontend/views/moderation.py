from apps.frontend.decorators import moderator_required
from apps.frontend.forms import ModerationDecisionForm
from apps.frontend.utils import flash_form_errors
from apps.projects.models import Project, ProjectStatus
from apps.projects.transitions import moderate_project
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError

from .projects import PAGE_SIZE

_LOGIN_URL = reverse_lazy("frontend:auth")


@login_required(login_url=_LOGIN_URL)
@moderator_required
def moderation_list(request):
    page_number = request.GET.get("page", 1)
    queryset = (
        Project.objects
        .filter(status=ProjectStatus.ON_MODERATION)
        .select_related("owner")
        .order_by("updated_at")
    )
    paginator   = Paginator(queryset, PAGE_SIZE)
    page_obj    = paginator.get_page(page_number)
    queue_count = paginator.count

    return render(request, "frontend/moderation_list.html", {
        "page_obj":      page_obj,
        "ProjectStatus": ProjectStatus,
        "queue_count":   queue_count,
    })


@require_POST
@login_required(login_url=_LOGIN_URL)
@moderator_required
def moderate_project_decide(request, pk):
    project = get_object_or_404(Project, pk=pk)

    form = ModerationDecisionForm(request.POST)
    if not form.is_valid():
        flash_form_errors(request, form)
        return redirect("frontend:moderation_list")

    decision = form.cleaned_data["decision"]
    comment  = form.cleaned_data["comment"]

    try:
        moderate_project(project, request.user, decision, comment)
        if decision == "approve":
            messages.success(request, f"Проект «{project.title}» опубликован!")
        else:
            messages.success(request, f"Проект «{project.title}» отклонён.")
    except DRFPermissionDenied:
        messages.error(request, "У вас нет прав для модерации.")
    except DRFValidationError:
        messages.error(request, "Проект уже прошёл модерацию или находится в недопустимом состоянии.")

    return redirect("frontend:moderation_list")
