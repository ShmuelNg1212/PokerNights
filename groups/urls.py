from django.urls import path

from . import views

urlpatterns = [
    path("g/new/", views.create_group, name="group_create"),
    path("g/<int:group_id>/members/<int:member_id>/role/", views.set_role, name="member_role"),
    path("g/<int:group_id>/members/<int:member_id>/remove/", views.remove_member, name="member_remove"),
]
