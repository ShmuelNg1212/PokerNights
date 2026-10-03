"""Read-only views of a finalized session."""

from dataclasses import dataclass

from ledger.models import Finalization

from .models import Transfer


@dataclass
class Outcome:
    finalization: Finalization
    results: list
    transfers: list

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
    return Outcome(finalization, results, transfers)
