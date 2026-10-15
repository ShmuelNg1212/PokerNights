"""Turning table alerts on and off for one phone. JSON in, an empty answer out."""

import json

from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST

from . import services


def _subscription(request):
    """The browser's PushSubscription as JSON, checked: an https endpoint and both keys."""
    try:
        found = json.loads(request.body)
        endpoint, keys = found["endpoint"], found.get("keys") or {}
        p256dh, auth = keys.get("p256dh", ""), keys.get("auth", "")
    except (ValueError, KeyError, TypeError, AttributeError):
        return None
    if not (isinstance(endpoint, str) and endpoint.startswith("https://") and len(endpoint) <= 1000):
        return None
    if not (isinstance(p256dh, str) and isinstance(auth, str) and 0 < len(p256dh) <= 200 and 0 < len(auth) <= 100):
        return None
    return endpoint, p256dh, auth


@require_POST
def subscribe(request):
    found = _subscription(request)
    if found is None:
        return HttpResponseBadRequest("Not a push subscription.")
    services.subscribe(request.user, *found)
    return HttpResponse(status=204)


@require_POST
def unsubscribe(request):
    try:
        endpoint = json.loads(request.body)["endpoint"]
    except (ValueError, KeyError, TypeError):
        return HttpResponseBadRequest("Not a push subscription.")
    services.unsubscribe(request.user, str(endpoint))
    return HttpResponse(status=204)
