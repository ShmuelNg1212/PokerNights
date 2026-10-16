"""A chat app's own browser: which one, and the card that asks the person to leave it.

A link tapped in Messenger, Facebook, Instagram, Viber, LINE or WeChat opens in that app's browser,
which cannot put the site on the home screen and forgets the login sooner. The front door
(Join, Sign up, Log in, Claim, Reset) shows a card that asks the person to open the same address
in Safari or Chrome before they make an account. Nothing redirects by itself: no way out of these
browsers is reliable, so every route is a tap, and Continue here always works.

The server decides from the user agent, so the card is in the first paint and works without
JavaScript. Continue here leaves a cookie for the browser session. WhatsApp and Telegram open links
in a view whose user agent reads as the plain browser; they cannot be told apart and get no card.
"""

import re
from urllib.parse import quote

from django.conf import settings
from django.utils.cache import patch_vary_headers

HERE_COOKIE = "chat_here"

# (pattern, the app's name). The first match names it. Messenger's markers come before Facebook's.
APPS = (
    (re.compile(r"Line/"), "LINE"),
    (re.compile(r"FBAN/Messenger|FB_IAB/MESSENGER"), "Messenger"),
    (re.compile(r"FBAN|FBAV|FB_IAB"), "Facebook"),
    (re.compile(r"Instagram"), "Instagram"),
    (re.compile(r"Viber"), "Viber"),
    (re.compile(r"MicroMessenger"), "WeChat"),
)
APPLE = re.compile(r"iPhone|iPad|iPod")
ANDROID = re.compile(r"Android")
# Where the person goes from a page. The invite or link in the address is what the card promises to keep.
CARRIES = (("/join/", "Your invite"), ("/claim/", "Your claim link"), ("/accounts/reset/", "Your reset link"))


def detect(agent):
    """(kind, app name): kind is "ios", "android" or "line", or None outside a chat app's browser on a phone."""
    for pattern, app in APPS:
        if pattern.search(agent):
            break
    else:
        return None, ""
    if not (APPLE.search(agent) or ANDROID.search(agent)):
        return None, ""
    return ("line" if app == "LINE" else "ios" if APPLE.search(agent) else "android"), app


class ChatBrowser:
    """Template context. Reading anything marks the request, so its answer varies by user agent."""

    def __init__(self, request):
        self.request = request
        request.chat_browser_read = False
        self._found = None

    def _detect(self):
        self.request.chat_browser_read = True
        if self._found is None:
            self._found = detect(self.request.headers.get("User-Agent", ""))
        return self._found

    @property
    def kind(self):
        """For every page: the home-screen sheet (install.js) reads it from <html>."""
        return self._detect()[0]

    @property
    def app(self):
        return self._detect()[1]

    @property
    def card(self):
        request = self.request
        if not settings.CHAT_BROWSER_CARD or not self.kind:
            return None
        if request.COOKIES.get(HERE_COOKIE) == "1" or request.GET.get("here") == "1":
            return None
        return self.kind

    @property
    def address(self):
        return self.request.build_absolute_uri()

    @property
    def intent(self):
        """Android: open this address in Chrome. If Chrome is missing, the fallback loads it here again."""
        request = self.request
        return (f"intent://{request.get_host()}{request.get_full_path()}#Intent;scheme={request.scheme};"
                f"package=com.android.chrome;S.browser_fallback_url={quote(self.address, safe='')};end")

    @property
    def line(self):
        """LINE opens an address that carries this in the phone's own browser (LINE's documented switch)."""
        return self._with("openExternalBrowser=1", absolute=True)

    @property
    def here(self):
        """Continue here without JavaScript: the same page, marked."""
        return self._with("here=1")

    @property
    def carries(self):
        request = self.request
        where = request.path + " " + request.GET.get("next", "")
        for part, words in CARRIES:
            if part in where:
                return words
        return ""

    def _with(self, pair, absolute=False):
        path = self.request.get_full_path()
        path += ("&" if "?" in path else "?") + pair
        return self.request.build_absolute_uri(path) if absolute else path


def chat_browser(request):
    return {"chat": ChatBrowser(request)}


class ChatBrowserVary:
    """Marks every answer that read the user agent, and remembers Continue here for the browser session."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if getattr(request, "chat_browser_read", False):
            patch_vary_headers(response, ["User-Agent"])
        if request.GET.get("here") == "1" and request.method == "GET":
            response.set_cookie(HERE_COOKIE, "1", samesite="Lax", secure=settings.SESSION_COOKIE_SECURE)
        return response
