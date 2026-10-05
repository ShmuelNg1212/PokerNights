from django.contrib import admin
from django.contrib.auth.decorators import login_not_required
from django.http import HttpResponse
from django.urls import include, path

from . import pwa


@login_not_required
def healthz(request):
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz, name="healthz"),
    path("sw.js", pwa.service_worker, name="service_worker"),
    path("offline/", pwa.offline, name="offline"),
    path("accounts/", include("accounts.urls")),
    path("", include("groups.urls")),
    path("", include("games.urls")),
    path("", include("ledger.urls")),
    path("", include("settlement.urls")),
    path("", include("web.urls")),
]
