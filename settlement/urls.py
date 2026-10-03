from django.urls import path

from . import views

urlpatterns = [
    path("s/<int:session_id>/finalize/", views.finalize, name="session_finalize"),
]
