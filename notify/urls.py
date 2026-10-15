from django.urls import path

from . import views

urlpatterns = [
    path("alerts/subscribe/", views.subscribe, name="alerts_subscribe"),
    path("alerts/unsubscribe/", views.unsubscribe, name="alerts_unsubscribe"),
]
