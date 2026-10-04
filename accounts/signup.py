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


# Functions that name who invited a newcomer, registered like CHECKS. Each takes the
# request and the path the person came from, and returns a name or None.
INVITERS = []


def invited_to(request, next_path: str):
    """The name of the group whose usable invite led here, or None."""
    for name_of in INVITERS:
        name = name_of(request, next_path)
        if name:
            return name
    return None
