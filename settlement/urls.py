from django.urls import path

from . import views

urlpatterns = [
    path("s/<int:session_id>/finalize/", views.finalize, name="session_finalize"),
    path("s/<int:session_id>/transfers/<int:transfer_id>/paid/", views.transfer_paid, name="transfer_paid"),
    path("s/<int:session_id>/transfers/<int:transfer_id>/unpaid/", views.transfer_unpaid, name="transfer_unpaid"),
]
