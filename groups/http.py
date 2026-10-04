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


def attempt_bound(request, form, action, *args, success="", **kwargs):
    """Keep business-rule failures with the bound form rather than a page toast."""
    try:
        result = action(*args, **kwargs)
    except RuleError as error:
        form.add_error(None, str(error))
        return None
    if success:
        messages.success(request, success)
    return result


def keep_form(request, key, form):
    """One redirect's non-sensitive input and errors; never passwords or tokens."""
    drafts = request.session.get("inline_forms", {})
    drafts[key] = {"data": {name: form.data.get(name, "") for name in form.fields},
                   "errors": {name: list(errors) for name, errors in form.errors.items()}}
    request.session["inline_forms"] = drafts


def take_form(request, key, form_class, **kwargs):
    drafts = request.session.get("inline_forms", {})
    draft = drafts.pop(key, None)
    request.session["inline_forms"] = drafts
    if draft is None:
        return form_class(**kwargs)
    form = form_class(draft["data"], **kwargs)
    form.is_valid()
    for name, errors in draft["errors"].items():
        if name not in form.errors:
            for error in errors:
                form.add_error(None if name == "__all__" else name, error)
    return form


def request_id_from(request) -> uuid.UUID:
    """The form's request_id, or a fresh one when a client sends none or a bad one."""
    try:
        return uuid.UUID(request.POST.get("request_id", ""))
    except ValueError:
        return uuid.uuid4()
