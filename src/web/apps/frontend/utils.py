from django.contrib import messages


def flash_form_errors(request, form) -> None:
    for field_errors in form.errors.values():
        for error in field_errors:
            messages.error(request, error)
