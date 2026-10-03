from django.conf import settings
from django.db import models
from django.db.models import F, Q

from games.models import GameSession, Participant
from ledger.models import Finalization


class SettlementPlan(models.Model):
    """The who-pays-whom list for one finalization. Written once with it."""

    finalization = models.OneToOneField(Finalization, on_delete=models.PROTECT, related_name="plan")
    # False only if the exact search was skipped (more parties than a table can seat).
    proven_minimal = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Settlement plan of {self.finalization}"


class Transfer(models.Model):
    """One instruction: ``payer`` pays ``payee`` this amount. Never edited."""

    plan = models.ForeignKey(SettlementPlan, on_delete=models.PROTECT, related_name="transfers")
    position = models.PositiveIntegerField()
    payer = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name="transfers_to_pay")
    payee = models.ForeignKey(Participant, on_delete=models.PROTECT, related_name="transfers_to_receive")
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


class Payment(models.Model):
    """A record that money changed hands. The app records payments; it never moves money.

    Marking a transfer paid creates a payment linked to it. ``payer`` or
    ``payee`` is empty when that side is the banker (a later stage).
    """

    session = models.ForeignKey(GameSession, on_delete=models.PROTECT, related_name="payments")
    payer = models.ForeignKey(Participant, null=True, blank=True, on_delete=models.PROTECT, related_name="payments_made")
    payee = models.ForeignKey(Participant, null=True, blank=True, on_delete=models.PROTECT, related_name="payments_received")
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
            models.UniqueConstraint(fields=["session", "request_id"], name="payment_request_once"),
            models.UniqueConstraint(fields=["transfer"], condition=Q(active=True), name="payment_one_active_per_transfer"),
            models.CheckConstraint(condition=Q(amount__gt=0), name="payment_amount_positive"),
        ]
        indexes = [models.Index(fields=["session"], name="payment_session")]

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
