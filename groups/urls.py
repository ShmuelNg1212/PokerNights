from django.urls import path

from . import views

urlpatterns = [
    path("g/new/", views.create_group, name="group_create"),
    path("g/<int:group_id>/members/<int:member_id>/role/", views.set_role, name="member_role"),
    path("g/<int:group_id>/members/<int:member_id>/restore/", views.restore_member, name="member_restore"),
    path("g/<int:group_id>/me/name/", views.rename_self, name="member_rename_self"),
    path("g/<int:group_id>/members/add/", views.add_roster_player, name="member_add"),
    path("g/<int:group_id>/members/<int:member_id>/rename/", views.rename_member, name="member_rename"),
    path("g/<int:group_id>/members/<int:member_id>/reset-link/", views.create_password_reset, name="member_reset_link"),
    path("g/<int:group_id>/members/<int:member_id>/reset-link/cancel/", views.cancel_password_reset, name="member_reset_link_cancel"),
    path("g/<int:group_id>/invites/new/", views.create_invite, name="invite_create"),
    path("g/<int:group_id>/invites/<int:invite_id>/revoke/", views.revoke_invite, name="invite_revoke"),
    path("g/<int:group_id>/members/<int:member_id>/claim-link/", views.create_claim_link, name="member_claim_link"),
    path("g/<int:group_id>/members/<int:member_id>/claim-link/cancel/", views.cancel_claim_link, name="member_claim_link_cancel"),
    path("claim/<str:token>/", views.claim, name="claim"),
    path("join/<str:token>/", views.accept_invite, name="invite_accept"),
]
