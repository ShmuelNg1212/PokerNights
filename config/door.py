"""The front door: which arrival a signed-out screen plays (DESIGN.md, "Front door").

The full arrival plays once per browser session and a short one after that. The choice has to be
in the page before its first paint, so the server makes it from a cookie that lasts as long as
the browser session. The cookie holds nothing and nothing is stored on the server.
"""

from django.conf import settings

COOKIE = "door"


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


def door(request):
    return {"door": Door(request)}


class DoorCookie:
    """Remembers, for this browser session, that the full arrival has played."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(request, "door_opened", False):
            response.set_cookie(COOKIE, "1", samesite="Lax", secure=settings.SESSION_COOKIE_SECURE)
        return response
