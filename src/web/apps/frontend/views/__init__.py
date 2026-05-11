# Re-export all views so that urls.py (which does `from . import views`)
# continues to work without any changes.

from .applications import (
    application_list,
    EditApplicationView,
    project_applications,
    review_application_view,
    submit_application,
    WithdrawApplicationView,
)
from .auth import (
    AuthView,
    VerifyEmailView,
    logout_view,
    resend_email_code_view,
)
from .errors import error_403, error_404, error_500
from .cpprp import (
    cpprp_dashboard,
    cpprp_deadline_create,
    cpprp_deadline_delete,
    cpprp_deadline_toggle,
    cpprp_external_allowlist_bulk_add,
    cpprp_external_allowlist_toggle,
    cpprp_external_request_approve,
    cpprp_external_request_reject,
    cpprp_export_applications,
    cpprp_export_projects,
    cpprp_template_create,
    cpprp_template_delete,
    cpprp_template_toggle,
)
from .legal import personal_data_consent_view, privacy_policy_view
from .moderation import moderate_project_decide, moderation_list
from .profile import profile_view
from .student import student_overview
from .technologies import technology_list, technology_moderate
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

__all__ = [
    # auth
    "AuthView",
    "VerifyEmailView",
    "resend_email_code_view",
    "logout_view",
    # errors
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
    "submit_application",
    "application_list",
    "project_applications",
    "review_application_view",
    "WithdrawApplicationView",
    "EditApplicationView",
    # cpprp
    "cpprp_dashboard",
    "cpprp_deadline_create",
    "cpprp_deadline_toggle",
    "cpprp_deadline_delete",
    "cpprp_template_create",
    "cpprp_template_toggle",
    "cpprp_template_delete",
    "cpprp_external_allowlist_bulk_add",
    "cpprp_external_request_approve",
    "cpprp_external_request_reject",
    "cpprp_external_allowlist_toggle",
    "cpprp_export_projects",
    "cpprp_export_applications",
    # legal
    "privacy_policy_view",
    "personal_data_consent_view",
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
