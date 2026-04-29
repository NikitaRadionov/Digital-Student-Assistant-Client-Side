import csv

from apps.base.admin_unfold import UnfoldModelAdmin
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path

from .models import Application


@admin.register(Application)
class ApplicationAdmin(UnfoldModelAdmin):
    list_display = ("id", "project", "applicant", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("project__title", "applicant__username", "applicant__email")
    actions = ("export_selected_as_csv",)
    change_list_template = "admin/applications/application/change_list.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "export-all/",
                self.admin_site.admin_view(self.export_all_as_csv_view),
                name="applications_application_export_all",
            ),
        ]
        return custom_urls + urls

    def export_all_as_csv_view(self, request):
        return self.export_selected_as_csv(request, Application.objects.order_by("pk"))

    @admin.action(description="Export selected applications as CSV")
    def export_selected_as_csv(self, request, queryset):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="applications-export.csv"'
        response.write("\ufeff")  # BOM for Excel UTF-8 compatibility

        writer = csv.writer(response)
        writer.writerow(
            [
                "id",
                "project_id",
                "project_title",
                "applicant_id",
                "applicant_email",
                "status",
                "created_at",
            ]
        )
        for application in queryset.select_related("project", "applicant").order_by("pk"):
            writer.writerow(
                [
                    application.pk,
                    application.project_id,
                    application.project.title,
                    application.applicant_id,
                    application.applicant.email,
                    application.status,
                    (
                        application.created_at.strftime("%Y-%m-%d %H:%M")
                        if application.created_at
                        else ""
                    ),
                ]
            )
        return response
