from django.urls import path

from . import views

urlpatterns = [
    path("s/<int:session_id>/finalize/", views.finalize, name="session_finalize"),
    path("n/<int:night_id>/close/", views.close_night, name="night_close"),
    path("n/<int:night_id>/transfers/<int:transfer_id>/paid/", views.transfer_paid, name="transfer_paid"),
    path("n/<int:night_id>/transfers/<int:transfer_id>/unpaid/", views.transfer_unpaid, name="transfer_unpaid"),
]
