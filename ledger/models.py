from django.conf import settings
from django.db import models
from django.db.models import F, Q

from games.models import GameSession, Participant, SettingsVersion, Unit
from groups.models import GameGroup, GroupRakeAccount, Member

# Every amount below is an integer in the session's unit: centavos in a pesos
# game, whole chips in a chips game. Nothing converts between the two.


class BuyIn(models.Model):
    """One buy-in or rebuy. Append-only: its amount never changes.

    A mistake is corrected by a BuyInReversal and, if needed, a new BuyIn.
    """

    session = models.ForeignKey(GameSession, on_delete=models.PROTECT, related_name="buy_ins")
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name="buy_ins")
    settings_version = models.ForeignKey(SettingsVersion, on_delete=models.PROTECT, related_name="+")
    amount = models.BigIntegerField()
    # Sent by the form. A repeated submission carries the same value and creates nothing.
    request_id = models.UUIDField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["session", "request_id"], name="buy_in_request_once"),
            models.CheckConstraint(condition=Q(amount__gt=0), name="buy_in_amount_positive"),
        ]
        indexes = [models.Index(fields=["participant"], name="buy_in_participant")]

    @property
    def rake_amount(self):
        return self.rake_entry.amount if hasattr(self, "rake_entry") else 0

    @property
    def recorded_unit(self):
        return self.rake_entry.unit if hasattr(self, "rake_entry") else self.session.unit

    @property
    def playable_amount(self):
        return self.amount - self.rake_amount

    def __str__(self):
        return f"Buy-in of {self.amount} for participant {self.participant_id}"


class RakeEntry(models.Model):
    """Immutable fee collected from one gross buy-in, including explicit zero fees."""

    buy_in = models.OneToOneField(BuyIn, on_delete=models.PROTECT, related_name="rake_entry")
    account = models.ForeignKey(GroupRakeAccount, on_delete=models.PROTECT, related_name="entries")
    amount = models.BigIntegerField()
    unit = models.CharField(max_length=8, choices=Unit.choices)
    rake_mode = models.CharField(max_length=8)
    rake_basis_points = models.PositiveIntegerField(default=0)
    rake_flat = models.BigIntegerField(default=0)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=Q(amount__gte=0), name="rake_amount_not_negative"),
            models.CheckConstraint(condition=Q(unit__in=["php", "chips"]), name="rake_unit_valid"),
        ]


class BuyInReversal(models.Model):
    """Voids one buy-in, with a reason. The buy-in row stays in the log."""

    buy_in = models.OneToOneField(BuyIn, on_delete=models.PROTECT, related_name="reversal")
    reason = models.CharField(max_length=255)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reversal of buy-in {self.buy_in_id}"


class CountEntry(models.Model):
    """What a player says they have at the end of a set, typed on their own phone. Not a count yet.

    It is a statement for the host to confirm; it is never cashed out or added to a result
    by itself. A change adds a row with the next version; rows are never edited.
    ``is_current`` marks the one statement in force for a player.
    """

    session = models.ForeignKey(GameSession, on_delete=models.PROTECT, related_name="count_entries")
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name="count_entries")
    amount = models.BigIntegerField()
    version = models.PositiveIntegerField(default=1)
    is_current = models.BooleanField(default=True)
    request_id = models.UUIDField()
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["participant"], condition=Q(is_current=True), name="count_entry_one_current"),
            models.UniqueConstraint(fields=["participant", "version"], name="count_entry_version_unique"),
            models.UniqueConstraint(fields=["session", "request_id"], name="count_entry_request_once"),
            models.CheckConstraint(condition=Q(amount__gte=0), name="count_entry_not_negative"),
        ]

    def __str__(self):
        return f"Entered count v{self.version} of {self.amount} by participant {self.participant_id}"


class FinalCount(models.Model):
    """A host's confirmation of what a player has at the end of a set. Not yet a cash-out.

    "Not counted" (no current row) and "counted, zero" (a row with amount 0) are
    different. A correction adds a row with the next version; rows are never
    edited. ``is_current`` marks the one count in force for a player.
    """

    session = models.ForeignKey(GameSession, on_delete=models.PROTECT, related_name="final_counts")
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name="final_counts")
    amount = models.BigIntegerField()
    version = models.PositiveIntegerField(default=1)
    is_current = models.BooleanField(default=True)
    request_id = models.UUIDField()
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    # The player's own statement that this confirmation accepted, when it came from one.
    entry = models.ForeignKey(CountEntry, null=True, blank=True, on_delete=models.PROTECT, related_name="confirmations")
    created_at = models.DateTimeField(auto_now_add=True)
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["participant"], condition=Q(is_current=True), name="final_count_one_current"),
            models.UniqueConstraint(fields=["participant", "version"], name="final_count_version_unique"),
            models.UniqueConstraint(fields=["session", "request_id"], name="final_count_request_once"),
            models.CheckConstraint(condition=Q(amount__gte=0), name="final_count_not_negative"),
        ]

    def __str__(self):
        return f"Final count v{self.version} of {self.amount} for participant {self.participant_id}"


class CashOutBatch(models.Model):
    """One "cash out counted players" action: who did it and when.

    Its ``request_id`` is unique per set, so sending the same confirmation
    again records nothing twice.
    """

    session = models.ForeignKey(GameSession, on_delete=models.PROTECT, related_name="cash_out_batches")
    request_id = models.UUIDField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["session", "request_id"], name="cash_out_batch_request_once"),
        ]

    def __str__(self):
        return f"Cash-out batch of set {self.session_id}"


class CashOut(models.Model):
    """What a player takes off the table. A player can cash out in several steps. Append-only.

    A cash-out of zero is a real record: the player lost everything. ``kind``
    says whether the player played on afterwards (``partial``) or was done
    (``final``). The amount never changes; ``kind`` is a classification and
    becomes ``partial`` again if the player returns to play.
    """

    class Kind(models.TextChoices):
        PARTIAL = "partial", "Partial"
        FINAL = "final", "Final"

    session = models.ForeignKey(GameSession, on_delete=models.PROTECT, related_name="cash_outs")
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name="cash_outs")
    amount = models.BigIntegerField()
    kind = models.CharField(max_length=8, choices=Kind.choices, default=Kind.FINAL)
    # The confirmed count that this cash-out records, when it came from one.
    final_count = models.OneToOneField(
        FinalCount, null=True, blank=True, on_delete=models.PROTECT, related_name="cash_out"
    )
    batch = models.ForeignKey(CashOutBatch, null=True, blank=True, on_delete=models.PROTECT, related_name="cash_outs")
    request_id = models.UUIDField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["session", "request_id"], name="cash_out_request_once"),
            models.CheckConstraint(condition=Q(amount__gte=0), name="cash_out_amount_not_negative"),
            models.CheckConstraint(condition=Q(kind__in=["partial", "final"]), name="cash_out_kind_valid"),
        ]
        indexes = [models.Index(fields=["participant"], name="cash_out_participant")]

    def __str__(self):
        return f"Cash-out of {self.amount} for participant {self.participant_id}"


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

    ``amount`` is added to the participant's cash-outs at finalization. The app
    never creates one on its own.
    """

    class Mode(models.TextChoices):
        PLAYER = "player", "One named player"
        EQUAL = "equal", "Shared equally"

    session = models.ForeignKey(GameSession, on_delete=models.PROTECT, related_name="adjustments")
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name="adjustments")
    amount = models.BigIntegerField()
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
            models.CheckConstraint(condition=~Q(amount=0), name="adjustment_not_zero"),
        ]
        indexes = [models.Index(fields=["session"], name="adjustment_session")]

    def __str__(self):
        return f"Adjustment of {self.amount} for participant {self.participant_id}"


class Finalization(models.Model):
    """The frozen outcome of a session. Written once, inside the finalization transaction.

    A later correction adds a new revision and marks this one not current; it is never edited.
    """

    session = models.ForeignKey(GameSession, on_delete=models.PROTECT, related_name="finalizations")
    revision = models.PositiveIntegerField()
    is_current = models.BooleanField(default=True)
    unit = models.CharField(max_length=8, choices=Unit.choices, default=Unit.PHP)
    total_buy_in = models.BigIntegerField()
    total_rake = models.BigIntegerField(default=0)
    # Cash-outs plus any host override. With rake, equals total_buy_in.
    total_cash_out = models.BigIntegerField()
    # Cash-outs plus rake minus gross buy-ins, before any host override.
    raw_difference = models.BigIntegerField(default=0)
    settings_snapshot = models.JSONField()
    finalized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["session", "revision"]
        constraints = [
            models.UniqueConstraint(fields=["session", "revision"], name="finalization_revision_unique"),
            models.UniqueConstraint(fields=["session"], condition=Q(is_current=True), name="finalization_one_current"),
            models.CheckConstraint(condition=Q(total_buy_in=F("total_cash_out") + F("total_rake")), name="finalization_money_conserved"),
            models.CheckConstraint(condition=Q(total_rake__gte=0), name="finalization_rake_not_negative"),
        ]

    def __str__(self):
        return f"Finalization r{self.revision} of session {self.session_id}"


class PlayerResult(models.Model):
    """One player's frozen result in a finalized session. Statistics read only current rows.

    ``unit`` is repeated here so that a later leaderboard never adds pesos to chips.
    """

    finalization = models.ForeignKey(Finalization, on_delete=models.PROTECT, related_name="results")
    participant = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name="results")
    # Repeated from the session so that statistics read one table.
    member = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="results")
    group = models.ForeignKey(GameGroup, on_delete=models.PROTECT, related_name="+")
    game_date = models.DateField()
    unit = models.CharField(max_length=8, choices=Unit.choices, default=Unit.PHP)
    rake_total = models.BigIntegerField(default=0)
    buy_in_total = models.BigIntegerField()
    buy_in_count = models.PositiveIntegerField()
    cashed_out = models.BigIntegerField()  # what the player's cash-outs add up to
    adjustment = models.BigIntegerField(default=0)  # the player's share of a host override
    cash_out = models.BigIntegerField()  # cashed_out + adjustment
    net = models.BigIntegerField()  # cash_out − buy_in_total
    # Seconds the player was at the table while the set was in play, as it stood
    # when play ended. Empty for sets played before playing time was recorded.
    play_seconds = models.PositiveIntegerField(null=True, blank=True)
    is_current = models.BooleanField(default=True)

    class Meta:
        ordering = ["finalization", "participant__join_order"]
        constraints = [
            models.CheckConstraint(condition=Q(rake_total__gte=0, rake_total__lte=F("buy_in_total")), name="result_rake_valid"),
            models.UniqueConstraint(fields=["finalization", "participant"], name="result_once_per_finalization"),
            models.UniqueConstraint(fields=["participant"], condition=Q(is_current=True), name="result_one_current"),
            models.CheckConstraint(
                condition=Q(net=F("cash_out") - F("buy_in_total")), name="result_net_is_cash_out_minus_buy_ins"
            ),
            models.CheckConstraint(
                condition=Q(cash_out=F("cashed_out") + F("adjustment")), name="result_cash_out_includes_adjustment"
            ),
        ]
        indexes = [
            models.Index(fields=["member", "game_date"], condition=Q(is_current=True), name="result_member_date"),
            models.Index(fields=["group", "game_date"], condition=Q(is_current=True), name="result_group_date"),
        ]

    def __str__(self):
        return f"Result {self.net} for participant {self.participant_id}"
