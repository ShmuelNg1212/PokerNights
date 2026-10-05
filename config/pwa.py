"""What lets a phone install the site: the service worker and its offline page.

The worker has one job. When a page navigation fails for lack of a connection it shows
the offline page. It stores that page and nothing else, so no ledger page is ever shown
from a cache. Setting SERVICE_WORKER=False serves a worker that removes itself.
"""

from django.conf import settings
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.shortcuts import render

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
self.addEventListener("fetch", (event) => {
  if (event.request.mode !== "navigate") return;
  event.respondWith(fetch(event.request).catch(() => caches.match(OFFLINE)));
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
    body = WORKER if settings.SERVICE_WORKER else REMOVER
    response = HttpResponse(body, content_type="text/javascript; charset=utf-8")
    response["Cache-Control"] = "no-cache"
    return response


@login_not_required
def offline(request):
    """A self-contained page: it must render with no other request."""
    return render(request, "offline.html")


def flags(request):
    """Template context: whether pages register the service worker and offer the in-app numpad."""
    return {"service_worker": settings.SERVICE_WORKER, "numpad": settings.NUMPAD}
