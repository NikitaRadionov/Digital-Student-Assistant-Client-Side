from django.contrib import admin

from .models import Project, ProjectStatus


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "owner", "updated_at", "source_type", "created_at")
    list_filter = ("status", "owner", "source_type", "created_at")
    search_fields = ("title", "description", "owner__username", "owner__email")
    list_select_related = ("owner",)
    autocomplete_fields = ("owner",)
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 50
    actions = ("publish_selected", "archive_selected")

    @admin.action(description="Publish selected projects")
    def publish_selected(self, request, queryset):
        updated = queryset.exclude(status=ProjectStatus.PUBLISHED).update(
            status=ProjectStatus.PUBLISHED
        )
        self.message_user(request, f"Published {updated} project(s).")

    @admin.action(description="Archive selected projects")
    def archive_selected(self, request, queryset):
        updated = queryset.exclude(status=ProjectStatus.ARCHIVED).update(
            status=ProjectStatus.ARCHIVED
        )
        self.message_user(request, f"Archived {updated} project(s).")
