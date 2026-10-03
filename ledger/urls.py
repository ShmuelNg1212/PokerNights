from django.urls import path

from . import views

urlpatterns = [
    path("s/<int:session_id>/buyins/add/", views.buy_in_add, name="buy_in_add"),
    path("s/<int:session_id>/buyins/<int:buy_in_id>/reverse/", views.buy_in_reverse, name="buy_in_reverse"),
    path("s/<int:session_id>/cashouts/add/", views.cash_out_add, name="cash_out_add"),
    path("s/<int:session_id>/cashouts/<int:cash_out_id>/reverse/", views.cash_out_reverse, name="cash_out_reverse"),
    path("s/<int:session_id>/override/", views.override_add, name="override_add"),
    path("s/<int:session_id>/override/remove/", views.override_void, name="override_void"),
]
