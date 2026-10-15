"""What a player is told: a notice per player and set, and the phones that take notifications.

``group_id`` and ``session_id`` are plain integers, not foreign keys, as in ``audit``:
this app is a leaf, and a notice outlives nothing it points at.
"""

from django.conf import settings
from django.db import models


class Notice(models.Model):
    """A player was put in a set by someone else. Written once per player and set."""

    class Kind(models.TextChoices):
        OPEN = "open", "The set opened"
        ADDED = "added", "Added to an open set"
        NEXT = "next", "Carried into the next set"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notices")
    group_id = models.BigIntegerField()
    session_id = models.BigIntegerField()
    kind = models.CharField(max_length=8, choices=Kind.choices)
    title = models.CharField(max_length=120)
    body = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    actor_name = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "session_id"], name="notice_once_per_set")]
        indexes = [models.Index(fields=["user", "seen_at"], name="notice_unseen")]

    def __str__(self):
        return f"{self.title} → {self.user}"


class PushSubscription(models.Model):
    """One phone or browser that agreed to notifications. The endpoint is the push service's address for it."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_subscriptions")
    endpoint = models.URLField(max_length=1000, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} · {self.endpoint[:40]}"
