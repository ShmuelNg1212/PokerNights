from django.contrib import admin

from audit.admin import ReadOnlyAdmin

from .models import GameGroup, GroupRakeAccount, Invite, Member


@admin.register(GameGroup)
class GameGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "created_at")


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ("display_name", "group", "user", "role", "status")
    list_filter = ("role", "status")


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ("group", "expires_at", "use_count", "max_uses", "revoked_at")
    exclude = ("token_hash",)


@admin.register(GroupRakeAccount)
class GroupRakeAccountAdmin(ReadOnlyAdmin):
    list_display = ("group", "created_at")
