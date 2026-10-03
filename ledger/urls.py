from django.urls import path

from . import views

urlpatterns = [
    path("s/<int:session_id>/buyins/add/", views.buy_in_add, name="buy_in_add"),
    path("s/<int:session_id>/buyins/<int:buy_in_id>/reverse/", views.buy_in_reverse, name="buy_in_reverse"),
]
