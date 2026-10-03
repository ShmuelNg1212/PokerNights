from django.contrib import admin

from .models import GameSession, Participant, SettingsPreset, SettingsVersion, Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "seat_count")


@admin.register(SettingsPreset)
class SettingsPresetAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "game_type")


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ("__str__", "group", "state", "game_date")
    list_filter = ("state",)
    # The state and the chip rate change only through the services.
    readonly_fields = ("state", "rate_centavos", "rate_chips", "version", "started_at", "finalized_at")


@admin.register(SettingsVersion)
class SettingsVersionAdmin(admin.ModelAdmin):
    list_display = ("session", "number", "created_at")

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("member", "session", "status", "join_order")
