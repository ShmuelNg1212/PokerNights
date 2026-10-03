"""Small helpers shared by the POST views of every app."""

import uuid

from django.contrib import messages

from .errors import RuleError


def attempt(request, action, *args, success="", **kwargs):
    """Run a service call. A RuleError becomes an error message; the result is returned on success."""
    try:
        result = action(*args, **kwargs)
    except RuleError as error:
        messages.error(request, str(error))
        return None
    if success:
        messages.success(request, success)
    return result


def request_id_from(request) -> uuid.UUID:
    """The form's request_id, or a fresh one when a client sends none or a bad one."""
    try:
        return uuid.UUID(request.POST.get("request_id", ""))
    except ValueError:
        return uuid.uuid4()
