from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "owner", "status", "source_type", "created_at")
    list_filter = ("status", "source_type", "created_at")
    search_fields = ("title", "description", "owner__username", "owner__email")
