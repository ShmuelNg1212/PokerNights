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


# What happens right after an account is created, registered like CHECKS. Each takes the
# request, the new user and the path the person came from, and returns the address to go
# to, or None to leave the decision to the next one.
AFTER_SIGNUP = []


def after_signup(request, user, next_path: str):
    """Where a new user goes when an app has already finished what they came for, else None."""
    for hook in AFTER_SIGNUP:
        target = hook(request, user, next_path)
        if target:
            return target
    return None
