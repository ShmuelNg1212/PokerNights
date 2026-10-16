"""What lets a phone install the site: the service worker and its offline page.

The worker has two jobs. When a page navigation fails for lack of a connection it shows
the offline page; the front door is left to the browser, so the server sees a chat app's user agent. It stores that page and nothing else, so no ledger page is ever shown
from a cache. And it shows a table alert that the server pushed (notify/push.py), and opens
the set when the alert is tapped. Setting SERVICE_WORKER=False serves a worker that removes
itself, and with it the alerts.
"""

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import render
from django.templatetags.static import static

from notify import push

WORKER = """// PokerNights service worker: an offline page for failed navigations. Nothing else is cached.
const CACHE = "pokernights-offline-1";
const OFFLINE = "/offline/";
self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.add(new Request(OFFLINE, { cache: "reload" }))));
  self.skipWaiting();
});
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});
// The front door is left to the browser: a request the worker makes carries the worker's user agent,
// not a chat app's, and the page needs the chat app's to ask the person to leave it (config/chat_browser.py).
const FRONT_DOOR = /^\/(accounts|join|claim)\//;
self.addEventListener("fetch", (event) => {
  if (event.request.mode !== "navigate" || FRONT_DOOR.test(new URL(event.request.url).pathname)) return;
  event.respondWith(fetch(event.request).catch(() => caches.match(OFFLINE)));
});
// A table alert: the title, the line under it and the set to open. One per set (the tag).
self.addEventListener("push", (event) => {
  let data = {};
  try { data = event.data ? event.data.json() : {}; } catch (error) { data = {}; }
  event.waitUntil(self.registration.showNotification(data.title || "PokerNights", {
    body: data.body || "", tag: data.tag, icon: "__ICON__", data: { url: data.url || "/" },
  }));
});
// A tap opens the set: in the app's window if one is open, otherwise in a new one.
self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = new URL((event.notification.data && event.notification.data.url) || "/", self.location.origin).href;
  event.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((windows) => {
    const open = windows.find((client) => new URL(client.url).origin === self.location.origin && "focus" in client);
    if (!open) return self.clients.openWindow(url);
    return open.focus().then((client) => (client && "navigate" in client ? client.navigate(url) : client));
  }));
});
"""

# The kill switch: a worker that deletes every cache and unregisters itself.
REMOVER = """// PokerNights service worker, switched off: it removes itself and its cache.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.map((key) => caches.delete(key))))
      .then(() => self.registration.unregister())
  );
});
"""


@login_not_required
def service_worker(request):
    body = WORKER.replace("__ICON__", static("icons/app-192.png")) if settings.SERVICE_WORKER else REMOVER
    response = HttpResponse(body, content_type="text/javascript; charset=utf-8")
    response["Cache-Control"] = "no-cache"
    return response


@login_not_required
def offline(request):
    """A self-contained page: it must render with no other request."""
    return render(request, "offline.html")


# Launch screens for the installed app on an iPhone, one per screen: CSS width, CSS height and
# pixel ratio. A phone shows the image only on an exact match and otherwise its blank launch, so a
# size missing here costs that phone nothing. Portrait only, as the manifest. The images are rendered
# by web/tests/browser/make_splash.mjs, which keeps its own copy of this list.
SPLASH_SIZES = (
    (375, 667, 2),   # SE (2nd, 3rd), 8
    (414, 736, 3),   # 8 Plus
    (375, 812, 3),   # X, XS, 11 Pro, 12 mini, 13 mini
    (414, 896, 2),   # XR, 11
    (414, 896, 3),   # XS Max, 11 Pro Max
    (390, 844, 3),   # 12, 13, 14, 16e
    (428, 926, 3),   # 12 Pro Max, 13 Pro Max, 14 Plus
    (393, 852, 3),   # 14 Pro, 15, 15 Pro, 16
    (430, 932, 3),   # 14 Pro Max, 15 Plus, 15 Pro Max, 16 Plus
    (402, 874, 3),   # 16 Pro, 17, 17 Pro
    (440, 956, 3),   # 16 Pro Max, 17 Pro Max
    (420, 912, 3),   # Air
)


def splash_file(width, height, ratio):
    return f"splash/splash-{width * ratio}x{height * ratio}.png"


def startup_images():
    return [{"href": static(splash_file(w, h, r)),
             "media": f"(device-width: {w}px) and (device-height: {h}px) and (-webkit-device-pixel-ratio: {r}) and (orientation: portrait)"}
            for w, h, r in SPLASH_SIZES]


def flags(request):
    """Template context: the service worker, table alerts, the in-app numpad, one-trip answers to in-place actions, password reset links, the link preview picture and the iPhone launch screens."""
    return {"service_worker": settings.SERVICE_WORKER, "numpad": settings.NUMPAD, "answer_in_place": settings.ANSWER_IN_PLACE, "install_prompt": settings.INSTALL_PROMPT,
            "reset_links": settings.RESET_LINKS, "arrival_marks": settings.ARRIVAL_MARKS,
            # Table alerts in the header need the worker that shows them and both keys (notify/push.py).
            "push_alerts": settings.SERVICE_WORKER and push.enabled(), "vapid_public_key": settings.VAPID_PUBLIC_KEY,
            # A chat app fetching a link needs the picture's full address, host included.
            "link_preview_image": request.build_absolute_uri(static("branding/link-preview.png")),
            "startup_images": startup_images()}
