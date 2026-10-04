from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


class GameGroup(models.Model):
    """The people who play together. All tables, sessions and results belong to one group."""

    name = models.CharField(max_length=60)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    # An archived group is hidden from every member until a host restores it. Nothing is removed.
    archived_at = models.DateTimeField(null=True, blank=True)
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )

    def __str__(self):
        return self.name

    @property
    def is_archived(self):
        return self.archived_at is not None


class GroupRakeAccount(models.Model):
    """The group’s collected rake identity. Its totals are ledger queries."""

    group = models.OneToOneField(GameGroup, on_delete=models.PROTECT, related_name="rake_account")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rake — {self.group}"


class Member(models.Model):
    """A person in a group's roster. ``user`` is empty for a player without a login."""

    class Role(models.TextChoices):
        HOST = "host", "Host"
        PLAYER = "player", "Player"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        REMOVED = "removed", "Removed"

    group = models.ForeignKey(GameGroup, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="memberships"
    )
    display_name = models.CharField(max_length=60)
    contact = models.CharField(max_length=120, blank=True)
    role = models.CharField(max_length=8, choices=Role.choices, default=Role.PLAYER)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["group", "user"], condition=Q(user__isnull=False), name="member_one_per_user_per_group"
            ),
            models.UniqueConstraint(
                Lower("display_name"), "group", condition=Q(status="active"), name="member_active_name_unique"
            ),
            models.CheckConstraint(condition=Q(role__in=["host", "player"]), name="member_role_valid"),
            models.CheckConstraint(condition=Q(status__in=["active", "removed"]), name="member_status_valid"),
        ]
        indexes = [models.Index(fields=["user", "status"], name="member_user_status")]

    def __str__(self):
        return self.display_name

    @property
    def is_host(self):
        return self.role == self.Role.HOST and self.status == self.Status.ACTIVE

    @property
    def has_login(self):
        return self.user_id is not None


class Invite(models.Model):
    """A link that lets a signed-in user enter the group. Only the token's hash is stored."""

    group = models.ForeignKey(GameGroup, on_delete=models.CASCADE, related_name="invites")
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=20)
    use_count = models.PositiveIntegerField(default=0)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(condition=Q(use_count__lte=models.F("max_uses")), name="invite_uses_within_limit"),
        ]

    def __str__(self):
        return f"Invite to {self.group} (expires {self.expires_at:%Y-%m-%d})"
