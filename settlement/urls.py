from django.urls import path

from . import views

urlpatterns = [
    path("g/<int:group_id>/members/<int:member_id>/remove/", views.member_remove, name="member_remove"),
    path("s/<int:session_id>/finalize/", views.finalize, name="session_finalize"),
    path("n/<int:night_id>/close/", views.close_night, name="night_close"),
    path("n/<int:night_id>/archive/", views.night_archive, name="night_archive"),
    path("n/<int:night_id>/restore/", views.night_restore, name="night_restore"),
    path("n/<int:night_id>/delete/", views.night_delete, name="night_delete"),
    path("n/<int:night_id>/transfers/<int:transfer_id>/paid/", views.transfer_paid, name="transfer_paid"),
    path("n/<int:night_id>/transfers/<int:transfer_id>/unpaid/", views.transfer_unpaid, name="transfer_unpaid"),
]
