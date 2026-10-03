from django.urls import path

from . import views

urlpatterns = [
    path("g/new/", views.create_group, name="group_create"),
    path("g/<int:group_id>/members/<int:member_id>/role/", views.set_role, name="member_role"),
    path("g/<int:group_id>/members/<int:member_id>/remove/", views.remove_member, name="member_remove"),
    path("g/<int:group_id>/members/add/", views.add_roster_player, name="member_add"),
    path("g/<int:group_id>/members/<int:member_id>/rename/", views.rename_member, name="member_rename"),
    path("g/<int:group_id>/invites/new/", views.create_invite, name="invite_create"),
    path("g/<int:group_id>/invites/<int:invite_id>/revoke/", views.revoke_invite, name="invite_revoke"),
    path("join/<str:token>/", views.accept_invite, name="invite_accept"),
]
