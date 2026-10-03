from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("g/<int:group_id>/", views.group, name="group"),
]
