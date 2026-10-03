from django.contrib import admin

from .models import GameGroup, Invite, Member


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
