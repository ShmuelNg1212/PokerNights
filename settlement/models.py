from types import SimpleNamespace

from django.conf import settings
from django.db import models
from django.db.models import F, Q

from games.models import GameNight
from groups.models import Member

# Settle-up belongs to a session (GameNight), not to one set: it nets each
# player's results over all sets. A player has one participant row per set, so
# transfers and payments name members.


class SettlementPlan(models.Model):
    """The who-pays-whom list of a session. Written when the session is closed.

    Reopening the session marks the plan not current; it is never edited or
    removed. Closing again writes a new plan.
    """

    night = models.ForeignKey(GameNight, on_delete=models.PROTECT, related_name="plans")
    is_current = models.BooleanField(default=True)
    # False only if the exact search was skipped (more parties than a table can seat).
    proven_minimal = models.BooleanField(default=True)
    # The group's rake rule when the list was made: True when the rake was paid into the rake fund.
    rake_to_fund = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    # Filled when the host reopens the session: who, when and why this list stopped being current.
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    void_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["night", "created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["night"], condition=Q(is_current=True), name="plan_one_current"),
        ]

    def __str__(self):
        return f"Settlement plan of {self.night}"


RAKE_FUND = "Rake fund"
# Stands in for a member where a page names the other side of a transfer into the rake fund.
RAKE_FUND_PARTY = SimpleNamespace(pk=None, display_name=RAKE_FUND)


class Transfer(models.Model):
    """One instruction: ``payer`` pays ``payee`` this amount. Never edited.

    A transfer into the group's rake fund has no payee and ``to_rake_fund`` set.
    """

    plan = models.ForeignKey(SettlementPlan, on_delete=models.PROTECT, related_name="transfers")
    position = models.PositiveIntegerField()
    payer = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="transfers_to_pay")
    payee = models.ForeignKey(Member, null=True, blank=True, on_delete=models.PROTECT, related_name="transfers_to_receive")
    to_rake_fund = models.BooleanField(default=False)
    amount = models.BigIntegerField()

    class Meta:
        ordering = ["plan", "position"]
        constraints = [
            models.UniqueConstraint(fields=["plan", "position"], name="transfer_position_unique"),
            models.CheckConstraint(condition=Q(amount__gt=0), name="transfer_amount_positive"),
            models.CheckConstraint(condition=~Q(payer=F("payee")), name="transfer_payer_is_not_payee"),
            models.CheckConstraint(
                condition=Q(payee__isnull=False, to_rake_fund=False) | Q(payee__isnull=True, to_rake_fund=True),
                name="transfer_one_payee",
            ),
        ]

    def __str__(self):
        return f"Transfer {self.amount} from {self.payer_id} to {self.payee_id or RAKE_FUND}"

    @property
    def payee_label(self):
        return RAKE_FUND if self.to_rake_fund else self.payee.display_name

    @property
    def payee_party(self):
        """The payee, or the rake fund in a member's place."""
        return RAKE_FUND_PARTY if self.to_rake_fund else self.payee


class CarriedTransfer(models.Model):
    """An unpaid transfer of an earlier session that a later session's list took over.

    Written when the later session is closed. It is in force while ``plan`` is that session's
    current list: reopening the session retires the plan, and the transfer is unpaid again
    without any row being changed. A transfer in force is neither paid nor unpaid.
    """

    transfer = models.ForeignKey(Transfer, on_delete=models.PROTECT, related_name="carries")
    plan = models.ForeignKey(SettlementPlan, on_delete=models.PROTECT, related_name="carried")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["plan", "transfer"]
        constraints = [
            models.UniqueConstraint(fields=["transfer", "plan"], name="carry_once_per_plan"),
        ]

    def __str__(self):
        return f"Transfer {self.transfer_id} carried into plan {self.plan_id}"


class Payment(models.Model):
    """A record that money changed hands. The app records payments; it never moves money.

    Marking a transfer paid creates a payment linked to it. A payment with no
    transfer was made at the table while the session was open (ADR 0002); closing
    subtracts it from what is still owed. It names both players.
    """

    night = models.ForeignKey(GameNight, on_delete=models.PROTECT, related_name="payments")
    payer = models.ForeignKey(Member, null=True, blank=True, on_delete=models.PROTECT, related_name="payments_made")
    payee = models.ForeignKey(Member, null=True, blank=True, on_delete=models.PROTECT, related_name="payments_received")
    amount = models.BigIntegerField()
    transfer = models.ForeignKey(Transfer, null=True, blank=True, on_delete=models.PROTECT, related_name="payments")
    # False once a PaymentReversal exists. Kept on the row so the database can
    # guarantee at most one active payment per transfer.
    active = models.BooleanField(default=True)
    request_id = models.UUIDField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.UniqueConstraint(fields=["night", "request_id"], name="payment_request_once"),
            models.UniqueConstraint(fields=["transfer"], condition=Q(active=True), name="payment_one_active_per_transfer"),
            models.CheckConstraint(condition=Q(amount__gt=0), name="payment_amount_positive"),
            models.CheckConstraint(
                condition=Q(transfer__isnull=False)
                | (Q(payer__isnull=False) & Q(payee__isnull=False) & ~Q(payer=F("payee"))),
                name="payment_at_table_names_two_players",
            ),
        ]
        indexes = [models.Index(fields=["night"], name="payment_night")]

    def __str__(self):
        return f"Payment {self.amount} from {self.payer_id} to {self.payee_id or RAKE_FUND}"

    @property
    def payee_label(self):
        """A payment of a transfer into the rake fund has no payee."""
        return self.payee.display_name if self.payee_id else RAKE_FUND


class PaymentReversal(models.Model):
    """Voids one payment record, for example a transfer marked paid by mistake."""

    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name="reversal")
    reason = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reversal of payment {self.payment_id}"
