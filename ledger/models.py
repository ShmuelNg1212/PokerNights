from django.conf import settings
from django.db import models
from django.db.models import Q

from games.models import GameSession, Participant, SettingsVersion
from groups.models import GameGroup, Member


class BuyIn(models.Model):
    """One buy-in or rebuy. Append-only: its amount and chips never change.

    A mistake is corrected by a BuyInReversal and, if needed, a new BuyIn.
    """

    session = models.ForeignKey(GameSession, on_delete=models.PROTECT, related_name="buy_ins")
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name="buy_ins")
    settings_version = models.ForeignKey(SettingsVersion, on_delete=models.PROTECT, related_name="+")
    amount_centavos = models.BigIntegerField()
    chips = models.BigIntegerField()
    # Sent by the form. A repeated submission carries the same value and creates nothing.
    request_id = models.UUIDField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["session", "request_id"], name="buy_in_request_once"),
            models.CheckConstraint(condition=Q(amount_centavos__gt=0), name="buy_in_amount_positive"),
            models.CheckConstraint(condition=Q(chips__gt=0), name="buy_in_chips_positive"),
        ]
        indexes = [models.Index(fields=["participant"], name="buy_in_participant")]

    def __str__(self):
        return f"Buy-in {self.amount_centavos} centavos for participant {self.participant_id}"


class BuyInReversal(models.Model):
    """Voids one buy-in, with a reason. The buy-in row stays in the log."""

    buy_in = models.OneToOneField(BuyIn, on_delete=models.PROTECT, related_name="reversal")
    reason = models.CharField(max_length=255)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reversal of buy-in {self.buy_in_id}"


class CashOut(models.Model):
    """Chips a player hands in. A player can cash out in several steps. Append-only.

    A cash-out of zero chips is a real record: the player lost everything.
    """

    session = models.ForeignKey(GameSession, on_delete=models.PROTECT, related_name="cash_outs")
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name="cash_outs")
    chips = models.BigIntegerField()
    request_id = models.UUIDField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["session", "request_id"], name="cash_out_request_once"),
            models.CheckConstraint(condition=Q(chips__gte=0), name="cash_out_chips_not_negative"),
        ]
        indexes = [models.Index(fields=["participant"], name="cash_out_participant")]

    def __str__(self):
        return f"Cash-out of {self.chips} chips for participant {self.participant_id}"


class CashOutReversal(models.Model):
    """Voids one cash-out, with a reason. The cash-out row stays in the log."""

    cash_out = models.OneToOneField(CashOut, on_delete=models.PROTECT, related_name="reversal")
    reason = models.CharField(max_length=255)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reversal of cash-out {self.cash_out_id}"


class BalanceAdjustment(models.Model):
    """A host's explicit answer to books that do not balance: who absorbs the difference.

    ``chips_delta`` is added to the participant's cashed-out chips at
    finalization. It is stored in chips, not pesos, so the centavo rounding rule
    still conserves the total. The app never creates one on its own.
    """

    class Mode(models.TextChoices):
        PLAYER = "player", "One named player"
        EQUAL = "equal", "Shared equally"

    session = models.ForeignKey(GameSession, on_delete=models.PROTECT, related_name="adjustments")
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name="adjustments")
    chips_delta = models.BigIntegerField()
    mode = models.CharField(max_length=8, choices=Mode.choices)
    note = models.CharField(max_length=255)
    # One override can create several rows (an equal share); they carry one request_id.
    request_id = models.UUIDField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["session", "request_id", "participant"], name="adjustment_request_once"),
            models.CheckConstraint(condition=~Q(chips_delta=0), name="adjustment_not_zero"),
        ]
        indexes = [models.Index(fields=["session"], name="adjustment_session")]

    def __str__(self):
        return f"Adjustment of {self.chips_delta} chips for participant {self.participant_id}"


class Finalization(models.Model):
    """The frozen outcome of a session. Written once, inside the finalization transaction.

    A later correction adds a new revision and marks this one not current; it is never edited.
    """

    session = models.ForeignKey(GameSession, on_delete=models.PROTECT, related_name="finalizations")
    revision = models.PositiveIntegerField()
    is_current = models.BooleanField(default=True)
    total_buy_in_centavos = models.BigIntegerField()
    total_cash_out_centavos = models.BigIntegerField()
    chips_issued = models.BigIntegerField()
    # Chips cashed out minus chips issued before any host override. Zero when the books balanced.
    raw_difference_chips = models.BigIntegerField(default=0)
    rate_centavos = models.BigIntegerField()
    rate_chips = models.BigIntegerField()
    settings_snapshot = models.JSONField()
    finalized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["session", "revision"]
        constraints = [
            models.UniqueConstraint(fields=["session", "revision"], name="finalization_revision_unique"),
            models.UniqueConstraint(fields=["session"], condition=Q(is_current=True), name="finalization_one_current"),
            models.CheckConstraint(
                condition=Q(total_buy_in_centavos=models.F("total_cash_out_centavos")),
                name="finalization_money_conserved",
            ),
        ]

    def __str__(self):
        return f"Finalization r{self.revision} of session {self.session_id}"


class PlayerResult(models.Model):
    """One player's frozen result in a finalized session. Statistics read only current rows."""

    finalization = models.ForeignKey(Finalization, on_delete=models.PROTECT, related_name="results")
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name="results")
    # Repeated from the session so that statistics read one table.
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="results")
    group = models.ForeignKey(GameGroup, on_delete=models.PROTECT, related_name="+")
    game_date = models.DateField()
    buy_in_total_centavos = models.BigIntegerField()
    buy_in_count = models.PositiveIntegerField()
    chips_cashed = models.BigIntegerField()
    adjustment_chips = models.BigIntegerField(default=0)
    # Value of chips_cashed + adjustment_chips at the session's chip rate.
    cash_out_centavos = models.BigIntegerField()
    net_centavos = models.BigIntegerField()
    is_current = models.BooleanField(default=True)

    class Meta:
        ordering = ["finalization", "participant__join_order"]
        constraints = [
            models.UniqueConstraint(fields=["finalization", "participant"], name="result_once_per_finalization"),
            models.UniqueConstraint(fields=["participant"], condition=Q(is_current=True), name="result_one_current"),
            models.CheckConstraint(
                condition=Q(net_centavos=models.F("cash_out_centavos") - models.F("buy_in_total_centavos")),
                name="result_net_is_cash_out_minus_buy_ins",
            ),
        ]
        indexes = [
            models.Index(fields=["member", "game_date"], condition=Q(is_current=True), name="result_member_date"),
            models.Index(fields=["group", "game_date"], condition=Q(is_current=True), name="result_group_date"),
        ]

    def __str__(self):
        return f"Result {self.net_centavos} centavos for participant {self.participant_id}"
