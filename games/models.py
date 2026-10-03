from django.conf import settings
from django.db import models
from django.db.models import F, Q

from groups.models import GameGroup


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
