from django.contrib import admin

from .models import SettingsPreset, Table


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "seat_count")


@admin.register(SettingsPreset)
class SettingsPresetAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "game_type")
