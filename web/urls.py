from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("g/<int:group_id>/", views.group, name="group"),
    path("n/<int:night_id>/", views.night, name="night"),
    path("s/<int:session_id>/", views.session, name="session"),
    path("s/<int:session_id>/state/", views.session_state, name="session_state"),
    path("s/<int:session_id>/log/", views.session_log, name="session_log"),
]
