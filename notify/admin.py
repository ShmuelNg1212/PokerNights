from django.contrib import admin

from .models import Notice, PushSubscription


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "kind", "created_at", "seen_at")
    list_filter = ("kind",)


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "last_sent_at")
