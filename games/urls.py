from django.urls import path

from . import views

urlpatterns = [
    path("g/<int:group_id>/tables/new/", views.create_table, name="table_create"),
    path("g/<int:group_id>/presets/new/", views.preset_form, name="preset_create"),
    path("g/<int:group_id>/presets/<int:preset_id>/", views.preset_form, name="preset_edit"),
    path("g/<int:group_id>/sessions/new/", views.session_new, name="session_create"),
    path("s/<int:session_id>/settings/", views.session_settings, name="session_settings"),
    path("s/<int:session_id>/transition/", views.session_transition, name="session_transition"),
    path("s/<int:session_id>/players/add/", views.participant_add, name="participant_add"),
    path("s/<int:session_id>/players/add-several/", views.participants_add, name="participants_add"),
    path("s/<int:session_id>/players/<int:participant_id>/withdraw/", views.participant_withdraw, name="participant_withdraw"),
    path("s/<int:session_id>/players/<int:participant_id>/left/", views.participant_left, name="participant_left"),
]
