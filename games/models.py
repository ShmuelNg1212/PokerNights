from django.conf import settings
from django.db import models
from django.db.models import F, Q

from groups.models import GameGroup, Member


class GameType(models.TextChoices):
    HOLDEM = "nlh", "No-Limit Hold'em"
    PLO = "plo", "Pot-Limit Omaha"
    OTHER = "other", "Other"


class StakesFields(models.Model):
    """Stakes and buy-in settings, shared by presets and by a session's settings versions.

    Money is integer centavos. ``chips_per_buy_in`` is the chip count issued for
    ``default_buy_in_centavos``; the two together define the chip rate.
    """

    small_blind_centavos = models.BigIntegerField()
    big_blind_centavos = models.BigIntegerField()
    min_buy_in_centavos = models.BigIntegerField()
    max_buy_in_centavos = models.BigIntegerField()
    default_buy_in_centavos = models.BigIntegerField()
    chips_per_buy_in = models.BigIntegerField()

    class Meta:
        abstract = True

    STAKES_FIELDS = (
        "small_blind_centavos", "big_blind_centavos", "min_buy_in_centavos",
        "max_buy_in_centavos", "default_buy_in_centavos", "chips_per_buy_in",
    )

    @staticmethod
    def stakes_constraints(prefix):
        return [
            models.CheckConstraint(
                condition=Q(small_blind_centavos__gt=0, big_blind_centavos__gte=F("small_blind_centavos")),
                name=f"{prefix}_blinds_valid",
            ),
            models.CheckConstraint(
                condition=Q(
                    min_buy_in_centavos__gt=0,
                    default_buy_in_centavos__gte=F("min_buy_in_centavos"),
                    max_buy_in_centavos__gte=F("default_buy_in_centavos"),
                ),
                name=f"{prefix}_buy_in_range_valid",
            ),
            models.CheckConstraint(condition=Q(chips_per_buy_in__gt=0), name=f"{prefix}_chips_positive"),
        ]

    def stakes(self) -> dict:
        return {name: getattr(self, name) for name in self.STAKES_FIELDS}


class SettingsPreset(StakesFields):
    """Reusable stakes for fast session setup. A session copies it; later edits change no session."""

    group = models.ForeignKey(GameGroup, on_delete=models.CASCADE, related_name="presets")
    name = models.CharField(max_length=60)
    game_type = models.CharField(max_length=8, choices=GameType.choices, default=GameType.HOLDEM)
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["group", "name"], condition=Q(archived_at__isnull=True), name="preset_active_name_unique"
            ),
            *StakesFields.stakes_constraints("preset"),
        ]

    def __str__(self):
        return self.name


class Table(models.Model):
    """A reusable, named playing place in a group. It has seats but no date."""

    group = models.ForeignKey(GameGroup, on_delete=models.CASCADE, related_name="tables")
    name = models.CharField(max_length=60)
    seat_count = models.PositiveSmallIntegerField(default=9)
    default_preset = models.ForeignKey(
        SettingsPreset, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(fields=["group", "name"], name="table_name_unique"),
            models.CheckConstraint(condition=Q(seat_count__gte=2, seat_count__lte=12), name="table_seat_count_valid"),
        ]

    def __str__(self):
        return self.name


class GameSession(models.Model):
    """One dated cash game at one table, with its own settings, players and money."""

    class State(models.TextChoices):
        SETUP = "setup", "Setup"
        OPEN = "open", "Open"
        RUNNING = "running", "Running"
        RECONCILIATION = "reconciliation", "Counting chips"
        FINALIZED = "finalized", "Finalized"
        CANCELED = "canceled", "Canceled"

    LIVE_STATES = (State.OPEN, State.RUNNING, State.RECONCILIATION)

    group = models.ForeignKey(GameGroup, on_delete=models.CASCADE, related_name="sessions")
    table = models.ForeignKey(Table, on_delete=models.PROTECT, related_name="sessions")
    # The Asia/Manila calendar date of the game. A game that runs past midnight keeps it.
    game_date = models.DateField()
    location = models.CharField(max_length=120, blank=True)
    game_type = models.CharField(max_length=8, choices=GameType.choices, default=GameType.HOLDEM)
    state = models.CharField(max_length=16, choices=State.choices, default=State.SETUP)
    seat_count = models.PositiveSmallIntegerField()
    # The chip rate in lowest terms. Set by the first accepted buy-in, cleared
    # when no accepted buy-in remains. While it is set, the session has money in it.
    rate_centavos = models.BigIntegerField(null=True, blank=True)
    rate_chips = models.BigIntegerField(null=True, blank=True)
    # Incremented by every write. Live screens poll it to learn that something changed.
    version = models.BigIntegerField(default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finalized_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-game_date", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=Q(state__in=["setup", "open", "running", "reconciliation", "finalized", "canceled"]),
                name="session_state_valid",
            ),
            models.CheckConstraint(
                condition=Q(rate_centavos__isnull=True, rate_chips__isnull=True)
                | Q(rate_centavos__gt=0, rate_chips__gt=0),
                name="session_rate_both_or_neither",
            ),
            models.CheckConstraint(condition=Q(seat_count__gte=2, seat_count__lte=12), name="session_seat_count_valid"),
        ]
        indexes = [
            models.Index(fields=["group", "state", "game_date"], name="session_group_state_date"),
            models.Index(fields=["table", "game_date"], name="session_table_date"),
        ]

    def __str__(self):
        return f"{self.table.name}, {self.game_date:%b %-d, %Y}"

    @property
    def rate(self):
        """The locked chip rate ``(centavos, chips)``, or None before the first buy-in."""
        if self.rate_centavos is None:
            return None
        return self.rate_centavos, self.rate_chips

    @property
    def is_live(self):
        return self.state in self.LIVE_STATES


class SettingsVersion(StakesFields):
    """The stakes of a session from one moment on. Never updated: a change adds a version."""

    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name="settings_versions")
    number = models.PositiveIntegerField()
    preset = models.ForeignKey(SettingsPreset, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["session", "number"]
        constraints = [
            models.UniqueConstraint(fields=["session", "number"], name="settings_version_number_unique"),
            *StakesFields.stakes_constraints("settings"),
        ]

    def __str__(self):
        return f"Settings v{self.number} of session {self.session_id}"


class Participant(models.Model):
    """A group member's place in one session."""

    class Status(models.TextChoices):
        JOINED = "joined", "Playing"
        WITHDRAWN = "withdrawn", "Withdrawn"
        LEFT = "left", "Left"

    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name="participants")
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="participations")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.JOINED)
    # Fixed order of first arrival. It breaks ties in rounding and in settle-up.
    join_order = models.PositiveIntegerField()
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["session", "join_order"]
        constraints = [
            models.UniqueConstraint(fields=["session", "member"], name="participant_once_per_session"),
            models.UniqueConstraint(fields=["session", "join_order"], name="participant_join_order_unique"),
            models.CheckConstraint(condition=Q(status__in=["joined", "withdrawn", "left"]), name="participant_status_valid"),
        ]
        indexes = [models.Index(fields=["member"], name="participant_member")]

    def __str__(self):
        return f"{self.member.display_name} in session {self.session_id}"
