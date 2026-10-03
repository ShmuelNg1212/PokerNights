from django.db import models
from django.db.models import F, Q

from games.models import Participant
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
    amount_centavos = models.BigIntegerField()

    class Meta:
        ordering = ["plan", "position"]
        constraints = [
            models.UniqueConstraint(fields=["plan", "position"], name="transfer_position_unique"),
            models.CheckConstraint(condition=Q(amount_centavos__gt=0), name="transfer_amount_positive"),
            models.CheckConstraint(condition=~Q(payer=F("payee")), name="transfer_payer_is_not_payee"),
        ]

    def __str__(self):
        return f"Transfer {self.amount_centavos} centavos from {self.payer_id} to {self.payee_id}"
