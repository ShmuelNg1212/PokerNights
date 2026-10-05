"""An action sent in place is answered with its page, in one trip instead of two.

A form on the set page or the session page posts, the view writes through a service and
answers with a redirect back to that page, and the browser fetches the page again. Each
trip costs the journey to the server and back. When the form says which page it was sent
from (``X-Answer-In-Place``, added by static/js/turbo-setup.js) and the view redirects to
exactly that page, this middleware draws the page in the same request and returns it,
with its address in ``X-In-Place-Location``.

Nothing else changes. Views still answer with redirects, so a form sent without the
header (no JavaScript, or any other client) gets the redirect it always got. The write is
committed before the page is drawn. The page is drawn by its ordinary view, as a GET
with no form data. If drawing fails, the redirect is returned and the browser fetches
the page itself. ``ANSWER_IN_PLACE=False`` switches it off.
"""

import io
import logging
from urllib.parse import urlsplit

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest

logger = logging.getLogger("pokernights")

ASKED = "X-Answer-In-Place"
ANSWERED = "X-In-Place-Location"
# What the middleware above this one has already worked out for the person, and must not be worked out twice.
CARRIED = ("session", "user", "auser", "_cached_user", "_acached_user", "_messages", "_dont_enforce_csrf_checks")
CSRF_STATE = ("CSRF_COOKIE", "CSRF_COOKIE_NEEDS_UPDATE")


def page_view(request, path, query) -> WSGIRequest:
    """A plain GET for ``path`` by the same person: no body, no form data, the same login session."""
    environ = dict(request.environ)
    environ.update({
        "REQUEST_METHOD": "GET", "PATH_INFO": path, "QUERY_STRING": query,
        "CONTENT_LENGTH": "0", "wsgi.input": io.BytesIO(b""),
    })
    for name in ("CONTENT_TYPE", "HTTP_X_ANSWER_IN_PLACE", "HTTP_X_REQUESTED_WITH"):
        environ.pop(name, None)
    view = WSGIRequest(environ)
    for name in CARRIED:
        if name in request.__dict__:
            setattr(view, name, request.__dict__[name])
    return view


class AnswerInPlace:
    """Placed after the session, login and message middleware, which the page is drawn inside."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        asked = request.headers.get(ASKED, "")
        if not (settings.ANSWER_IN_PLACE and request.method == "POST" and asked.startswith("/")):
            return response
        if response.status_code not in (302, 303) or not response.has_header("Location"):
            return response
        target, page = urlsplit(response["Location"]), urlsplit(asked)
        # Only a redirect back to the very page the form was sent from, on this site.
        if target.scheme or target.netloc or page.scheme or page.netloc or target.path != page.path:
            return response
        view = page_view(request, target.path, target.query)
        try:
            drawn = self.get_response(view)
            if hasattr(drawn, "render") and callable(drawn.render) and not getattr(drawn, "is_rendered", True):
                drawn = drawn.render()
        except Exception:
            logger.exception("Could not answer %s in place; sending the redirect to %s", request.path, target.path)
            return response
        finally:
            # A token made while drawing the page must reach the cookie the outer middleware sets.
            for name in CSRF_STATE:
                if name in view.META:
                    request.META[name] = view.META[name]
        if drawn.status_code != 200:
            logger.warning("Could not answer %s in place (the page answered %s); sending the redirect", request.path, drawn.status_code)
            return response
        drawn[ANSWERED] = target.path + ("?" + target.query if target.query else "")
        drawn["Cache-Control"] = "no-store"
        return drawn
