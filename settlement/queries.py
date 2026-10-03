"""Read-only views of a finalized session."""

from dataclasses import dataclass

from ledger.models import Finalization

from .models import Payment, Transfer


@dataclass
class Outcome:
    finalization: Finalization
    results: list
    transfers: list

    @property
    def paid_count(self) -> int:
        return sum(1 for t in self.transfers if t.paid)

    @property
    def status(self) -> str:
        """``settled``, ``partly`` or ``unsettled``. Derived from the paid marks; never stored."""
        if self.paid_count == len(self.transfers):
            return "settled"
        return "partly" if self.paid_count else "unsettled"

    @property
    def status_label(self) -> str:
        return {"settled": "Settled", "partly": "Partly settled", "unsettled": "Unsettled"}[self.status]

    def result_for(self, member_id):
        return next((r for r in self.results if r.member_id == member_id), None)

    def transfers_for(self, participant_id):
        """Transfers that this participant pays or receives."""
        return [t for t in self.transfers if participant_id in (t.payer_id, t.payee_id)]


def outcome(session):
    """The current results and transfers of a finalized session, or None."""
    finalization = Finalization.objects.filter(session=session, is_current=True).first()
    if finalization is None:
        return None
    results = list(
        finalization.results.select_related("participant__member").order_by("participant__join_order")
    )
    transfers = list(
        Transfer.objects.filter(plan__finalization=finalization)
        .select_related("payer__member", "payee__member")
        .order_by("position")
    )
    paid = {p.transfer_id: p for p in Payment.objects.filter(transfer__in=transfers, active=True)}
    for transfer in transfers:
        transfer.paid = paid.get(transfer.pk)
    return Outcome(finalization, results, transfers)
