import json
from functools import wraps

from apps.account.permissions import has_any_role
from apps.applications.models import Application, ApplicationStatus
from apps.applications.services import (
    create_application,
    delete_application,
    review_application_service,
    update_motivation,
)
from apps.frontend.forms import ApplicationFilterForm, MotivationForm, ReviewApplicationForm
from apps.frontend.utils import flash_form_errors
from apps.projects.models import Project, ProjectStatus
from apps.users.models import UserRole
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.exceptions import ValidationError as DRFValidationError

from .projects import PAGE_SIZE

_LOGIN_URL = reverse_lazy("frontend:auth")


def _require_student(request) -> HttpResponse | None:
    if not has_any_role(request.user, allowed={UserRole.STUDENT}, allow_staff=False):
        return HttpResponseBadRequest("Подавать заявки могут только студенты.")
    return None


def _htmx_unauth_response(request, pk: int) -> HttpResponse:
    if request.headers.get("HX-Request"):
        response = HttpResponse(status=204)
        response["HX-Redirect"] = reverse("frontend:auth") + f"?next=/projects/{pk}/"
        return response
    return JsonResponse(
        {"error": "unauthenticated", "redirect": reverse("frontend:auth")},
        status=401,
    )


def _toast_trigger(message: str, toast_type: str = "info") -> str:
    return json.dumps({"showToast": {"message": message, "type": toast_type}})


def _build_apply_response(request, source: str, project, application) -> HttpResponse:
    if source == "card":
        return render(request, "frontend/partials/apply_button.html", {
            "project":            project,
            "application_status": application.status,
            "ApplicationStatus":  ApplicationStatus,
            "ProjectStatus":      ProjectStatus,
        })
    return render(request, "frontend/partials/apply_action_detail.html", {
        "project":           project,
        "application":       application,
        "is_owner":          False,
        "ApplicationStatus": ApplicationStatus,
        "ProjectStatus":     ProjectStatus,
    })


def student_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse("frontend:auth") + "?next=/projects/")
        if err := _require_student(request):
            return err
        return view_func(request, *args, **kwargs)
    return wrapper


class OwnedSubmittedApplicationMixin:
    status_error_message: str = "Действие доступно только для заявки со статусом «На рассмотрении»."

    def dispatch(self, request, *args, **kwargs):
        application = get_object_or_404(
            Application.objects.select_related("project"),
            pk=kwargs["pk"],
        )
        if application.applicant != request.user:
            raise PermissionDenied
        if application.status != ApplicationStatus.SUBMITTED:
            messages.error(request, self.status_error_message)
            return redirect("frontend:project_list")
        self.application = application
        return super().dispatch(request, *args, **kwargs)


@require_POST
def submit_application(request, pk):
    if not request.user.is_authenticated:
        return _htmx_unauth_response(request, pk)
    if err := _require_student(request):
        return err

    project = get_object_or_404(Project, pk=pk)

    form = MotivationForm(request.POST)
    if not form.is_valid():
        error_msg = next(iter(form.errors.values()))[0]
        response  = HttpResponse(status=422)
        response["HX-Trigger"] = _toast_trigger(error_msg, "error")
        return response

    try:
        application, created = create_application(
            project=project,
            applicant=request.user,
            motivation=form.cleaned_data["motivation"],
        )
    except DRFValidationError:
        response = HttpResponse(status=422)
        response["HX-Trigger"] = _toast_trigger(
            "Проект в данный момент не принимает заявки.", "error"
        )
        return response

    toast_msg  = "Заявка успешно отправлена!" if created else "Вы уже подавали заявку на этот проект."
    toast_type = "success" if created else "info"

    response = _build_apply_response(
        request, request.POST.get("source", "detail"), project, application
    )
    response["HX-Trigger"] = _toast_trigger(toast_msg, toast_type)
    return response


@login_required(login_url=_LOGIN_URL)
def application_list(request):
    return redirect(reverse("frontend:project_list") + "?tab=applications")


@login_required(login_url=_LOGIN_URL)
def project_applications(request, pk):
    project = get_object_or_404(Project.objects.select_related("owner"), pk=pk)

    if project.owner != request.user and not request.user.is_staff:
        raise Http404

    filter_form   = ApplicationFilterForm(request.GET)
    filter_form.is_valid()
    status_filter = filter_form.cleaned_data.get("status", "")
    page_number   = request.GET.get("page", 1)

    queryset = (
        Application.objects
        .filter(project=project)
        .select_related("applicant")
        .order_by("-created_at")
    )
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    paginator = Paginator(queryset, PAGE_SIZE)
    page_obj  = paginator.get_page(page_number)

    counts = Application.objects.filter(project=project).aggregate(
        submitted=Count("pk", filter=Q(status=ApplicationStatus.SUBMITTED)),
        accepted=Count("pk",  filter=Q(status=ApplicationStatus.ACCEPTED)),
        rejected=Count("pk",  filter=Q(status=ApplicationStatus.REJECTED)),
    )

    return render(request, "frontend/project_applications.html", {
        "project":           project,
        "page_obj":          page_obj,
        "status_filter":     status_filter,
        "filter_form":       filter_form,
        "ApplicationStatus": ApplicationStatus,
        "ProjectStatus":     ProjectStatus,
        "counts":            counts,
        "total_count":       sum(counts.values()),
        "spots_left":        max(0, project.team_size - project.accepted_participants_count),
    })


@require_POST
@login_required(login_url=_LOGIN_URL)
def review_application_view(request, pk):
    application = get_object_or_404(
        Application.objects.select_related("project", "project__owner"),
        pk=pk,
    )

    form = ReviewApplicationForm(request.POST)
    if not form.is_valid():
        flash_form_errors(request, form)
        return redirect("frontend:project_applications", pk=application.project.pk)

    decision = form.cleaned_data["decision"]
    comment  = form.cleaned_data["comment"]

    try:
        review_application_service(application, request.user, decision, comment)
        messages.success(
            request,
            "Заявка принята!" if decision == "accept" else "Заявка отклонена.",
        )
    except DRFPermissionDenied:
        messages.error(request, "У вас нет прав для этого действия.")
    except DRFValidationError:
        messages.error(request, "Заявка не может быть обработана — её статус уже изменился.")

    return redirect("frontend:project_applications", pk=application.project.pk)


class WithdrawApplicationView(LoginRequiredMixin, OwnedSubmittedApplicationMixin, View):
    login_url            = _LOGIN_URL
    status_error_message = "Отозвать можно только заявку со статусом «На рассмотрении»."

    def post(self, request, pk):
        project_title = self.application.project.title
        delete_application(self.application)
        messages.success(request, f"Заявка на проект «{project_title}» отозвана.")
        return redirect("frontend:project_list")


class EditApplicationView(LoginRequiredMixin, OwnedSubmittedApplicationMixin, View):
    login_url            = _LOGIN_URL
    template_name        = "frontend/edit_application.html"
    status_error_message = "Редактировать можно только заявку со статусом «На рассмотрении»."

    def get(self, request, pk):
        form = MotivationForm(initial={"motivation": self.application.motivation})
        return render(request, self.template_name, self._build_context(form=form))

    def post(self, request, pk):
        form = MotivationForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, self._build_context(form=form))
        update_motivation(self.application, form.cleaned_data["motivation"])
        messages.success(request, "Мотивация обновлена.")
        return redirect("frontend:project_list")

    def _build_context(self, *, form: MotivationForm) -> dict:
        return {
            "application": self.application,
            "project":     self.application.project,
            "form":        form,
        }
