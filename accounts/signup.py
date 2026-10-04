"""Who may open the sign-up form when sign-up is not open to everyone.

Apps that can vouch for a newcomer register a check here; ``accounts`` does not
import them. A check takes the request and the path the person came from, and
returns True to allow sign-up.
"""

from django.conf import settings

CHECKS = []


def allowed(request, next_path: str) -> bool:
    if not settings.SIGNUP_REQUIRES_INVITE:
        return True
    return any(check(request, next_path) for check in CHECKS)
