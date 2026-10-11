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


class Transfer(models.Model):
    """One instruction: ``payer`` pays ``payee`` this amount. Never edited."""

    plan = models.ForeignKey(SettlementPlan, on_delete=models.PROTECT, related_name="transfers")
    position = models.PositiveIntegerField()
    payer = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="transfers_to_pay")
    payee = models.ForeignKey(Member, on_delete=models.PROTECT, related_name="transfers_to_receive")
    amount = models.BigIntegerField()

    class Meta:
        ordering = ["plan", "position"]
        constraints = [
            models.UniqueConstraint(fields=["plan", "position"], name="transfer_position_unique"),
            models.CheckConstraint(condition=Q(amount__gt=0), name="transfer_amount_positive"),
            models.CheckConstraint(condition=~Q(payer=F("payee")), name="transfer_payer_is_not_payee"),
        ]

    def __str__(self):
        return f"Transfer {self.amount} from {self.payer_id} to {self.payee_id}"


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

    Marking a transfer paid creates a payment linked to it. ``payer`` or
    ``payee`` is empty when that side is the banker (a later stage).
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
        ]
        indexes = [models.Index(fields=["night"], name="payment_night")]

    def __str__(self):
        return f"Payment {self.amount} from {self.payer_id} to {self.payee_id}"


class PaymentReversal(models.Model):
    """Voids one payment record, for example a transfer marked paid by mistake."""

    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name="reversal")
    reason = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reversal of payment {self.payment_id}"
