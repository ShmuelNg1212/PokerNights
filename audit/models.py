from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    """Append-only record of who did what. Never updated or deleted.

    ``group_id`` and ``session_id`` are plain integers, not foreign keys, so
    this app depends on no other app and the log survives any later cleanup.
    """

    group_id = models.BigIntegerField(null=True, blank=True)
    session_id = models.BigIntegerField(null=True, blank=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.BigIntegerField(null=True, blank=True)
    summary = models.CharField(max_length=255, blank=True)
    reason = models.CharField(max_length=255, blank=True)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["session_id", "created_at"], name="audit_session_time"),
            models.Index(fields=["group_id", "created_at"], name="audit_group_time"),
        ]

    def __str__(self):
        return f"{self.action} by {self.actor_id} at {self.created_at:%Y-%m-%d %H:%M}"
