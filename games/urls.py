from django.urls import path

from . import views

urlpatterns = [
    path("g/<int:group_id>/archive/", views.group_archive, name="group_archive"),
    path("g/<int:group_id>/restore/", views.group_restore, name="group_restore"),
    path("g/<int:group_id>/delete/", views.group_delete, name="group_delete"),
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
    path("s/<int:session_id>/draw/", views.seat_draw, name="seat_draw"),
    path("s/<int:session_id>/draw/seat/", views.seat_choose, name="seat_choose"),
    path("s/<int:session_id>/draw/late/", views.seat_late, name="seat_late"),
    path("n/<int:night_id>/next-set/", views.next_set, name="next_set"),
    path("n/<int:night_id>/announce/", views.night_announce, name="night_announce"),
    path("n/<int:night_id>/rsvp/", views.night_rsvp, name="night_rsvp"),
    path("n/<int:night_id>/seats/", views.night_seats, name="night_seats"),
    path("n/<int:night_id>/seat-now/", views.night_seat_now, name="night_seat_now"),
]
