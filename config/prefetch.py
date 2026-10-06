"""A page fetched ahead of a tap must not use up anything meant to be shown once.

Turbo fetches a link when the pointer or finger reaches it and marks the request
``X-Sec-Purpose: prefetch``. The page may never be shown. Flash messages and the session's
one-time values (a kept form, a new invite or reset link, typed counts) are therefore left exactly
as they were, and the prefetched page is rendered without the messages.
"""

import copy

# Session values that a view shows once and then removes.
ONE_TIME_KEYS = ("inline_forms", "new_invite_url", "new_reset_link", "count_drafts")


def is_prefetch(request) -> bool:
    return "prefetch" in request.headers.get("X-Sec-Purpose", "") or "prefetch" in request.headers.get("Sec-Purpose", "")


class _NoMessages:
    """Stands in for the message storage while a prefetch renders: nothing to show, nothing consumed."""

    used = False
    added_new = False

    def __init__(self, real):
        self._real = real

    def __iter__(self):
        return iter(())

    def __len__(self):
        return 0

    def add(self, level, message, extra_tags=""):
        return self._real.add(level, message, extra_tags)

    def update(self, response):
        return self._real.update(response)


class PrefetchLeavesOneTimeState:
    """Placed after the session and message middleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method != "GET" or not is_prefetch(request):
            return self.get_response(request)
        real = getattr(request, "_messages", None)
        # Copied, because a view changes these values in place before putting them back.
        kept = {key: copy.deepcopy(request.session[key]) for key in ONE_TIME_KEYS if key in request.session}
        if real is not None:
            request._messages = _NoMessages(real)
        try:
            response = self.get_response(request)
        finally:
            if real is not None:
                request._messages = real
            for key, value in kept.items():
                request.session[key] = value
        response["Cache-Control"] = "no-store"
        return response
