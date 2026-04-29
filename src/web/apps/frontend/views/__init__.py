# Re-export all views so that urls.py (which does `from . import views`)
# continues to work without any changes.

from .applications import (
    application_list,
    apply_to_project,
    edit_application,
    project_applications,
    review_application_view,
    submit_application,
    withdraw_application,
)
from .auth import (
    auth_view,
    error_403,
    error_404,
    error_500,
    logout_view,
    resend_email_code_view,
    verify_email_view,
)
from .cpprp import (
    cpprp_dashboard,
    cpprp_deadline_create,
    cpprp_deadline_delete,
    cpprp_deadline_toggle,
    cpprp_export_applications,
    cpprp_export_projects,
    cpprp_template_create,
    cpprp_template_delete,
    cpprp_template_toggle,
)
from .moderation import moderate_project_decide, moderation_list
from .profile import profile_view
from .projects import (
    initiative_project_create,
    project_create,
    project_delete,
    project_detail,
    project_edit,
    project_list,
    project_submit_moderation,
    recommendations_view,
    toggle_bookmark,
)
from .student import student_overview
from .technologies import technology_list, technology_moderate

__all__ = [
    # auth
    "auth_view",
    "verify_email_view",
    "resend_email_code_view",
    "logout_view",
    "error_403",
    "error_404",
    "error_500",
    # projects
    "project_list",
    "project_detail",
    "project_create",
    "project_edit",
    "project_submit_moderation",
    "project_delete",
    "recommendations_view",
    "toggle_bookmark",
    "initiative_project_create",
    # applications
    "apply_to_project",
    "submit_application",
    "application_list",
    "project_applications",
    "review_application_view",
    "withdraw_application",
    "edit_application",
    # cpprp
    "cpprp_dashboard",
    "cpprp_deadline_create",
    "cpprp_deadline_toggle",
    "cpprp_deadline_delete",
    "cpprp_template_create",
    "cpprp_template_toggle",
    "cpprp_template_delete",
    "cpprp_export_projects",
    "cpprp_export_applications",
    # moderation
    "moderation_list",
    "moderate_project_decide",
    # profile
    "profile_view",
    # technologies
    "technology_list",
    "technology_moderate",
    # student
    "student_overview",
]
