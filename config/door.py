"""The front door: which arrival a signed-out screen plays (DESIGN.md, "Front door").

The full arrival plays once per browser session and a short one after that. The choice has to be
in the page before its first paint, so the server makes it from a cookie that lasts as long as
the browser session. The cookie holds nothing and nothing is stored on the server.

The one page that follows a successful login plays the arrival into the app. A login marks its
answer with a second cookie that lasts half a minute; the first page a signed-in person is shown
reads it and removes it.
"""

from django.conf import settings
from django.contrib.auth.signals import user_logged_in

from .prefetch import is_prefetch

COOKIE = "door"
ARRIVED = "arrived"
ARRIVED_SECONDS = 30


def _logged_in(sender, request, user, **kwargs):
    """Every way in ends in Django's login(): the form, sign-up, a reset link, a claim."""
    if request is not None:
        request.door_arrived = True


user_logged_in.connect(_logged_in, dispatch_uid="config.door.logged_in")


class Door:
    """Template context. Reading ``arrival`` marks the request, so only a front-door page sets the cookie."""

    def __init__(self, request):
        self.request = request

    @property
    def on(self):
        return settings.DOOR_MOTION

    @property
    def arrival(self):
        if not settings.DOOR_MOTION or self.request.method != "GET":
            # A page that comes back refused answers with the refusal, not with an entrance.
            return ""
        if COOKIE in self.request.COOKIES:
            return "short"
        self.request.door_opened = True
        return "full"

    @property
    def welcome(self):
        """True on the one page shown after a login. A page fetched ahead of a tap may never be shown, so it does not count."""
        request = self.request
        if not settings.DOOR_MOTION or request.method != "GET" or request.COOKIES.get(ARRIVED) != "1":
            return False
        if is_prefetch(request) or not request.user.is_authenticated:
            return False
        request.door_welcomed = True
        return True


def door(request):
    return {"door": Door(request)}


class DoorCookie:
    """Remembers, for this browser session, that the full arrival has played, and carries a login to the page after it."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(request, "door_opened", False):
            response.set_cookie(COOKIE, "1", samesite="Lax", secure=settings.SESSION_COOKIE_SECURE)
        if getattr(request, "door_arrived", False) and settings.DOOR_MOTION:
            response.set_cookie(ARRIVED, "1", max_age=ARRIVED_SECONDS, samesite="Lax", secure=settings.SESSION_COOKIE_SECURE)
        elif getattr(request, "door_welcomed", False):
            response.delete_cookie(ARRIVED, samesite="Lax")
        return response
