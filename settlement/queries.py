"""Read-only views of finalized sets and of a session's settle-up."""

from dataclasses import dataclass, field

from groups.models import Member
from ledger.models import Finalization

from . import services
from .models import Payment, SettlementPlan, Transfer


@dataclass
class Outcome:
    """The frozen results of one set."""

    finalization: Finalization
    results: list

    def result_for(self, member_id):
        return next((r for r in self.results if r.member_id == member_id), None)


def outcome(session):
    """The current results of a finalized set, or None."""
    finalization = Finalization.objects.filter(session=session, is_current=True).first()
    if finalization is None:
        return None
    results = list(finalization.results.select_related("participant__member").order_by("participant__join_order"))
    return Outcome(finalization, results)


@dataclass
class Standing:
    member: Member
    net: int
    sets_played: int


@dataclass
class NightOutcome:
    """A session's results over its sets, and its transfers once it is closed."""

    standings: list
    plan: object = None
    transfers: list = field(default_factory=list)
    payments: list = field(default_factory=list)

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

    def standing_for(self, member_id):
        return next((s for s in self.standings if s.member.pk == member_id), None)

    def transfers_for(self, member_id):
        return [t for t in self.transfers if member_id in (t.payer_id, t.payee_id)]


def night_outcome(night) -> NightOutcome:
    rows = services.session_results(night)
    members = Member.objects.in_bulk([member_id for member_id, _, _ in rows])
    found = NightOutcome(standings=[Standing(members[m], net, played) for m, net, played in rows])
    found.plan = SettlementPlan.objects.filter(night=night).first()
    if found.plan is not None:
        found.transfers = list(
            Transfer.objects.filter(plan=found.plan).select_related("payer", "payee").order_by("position")
        )
        paid = {p.transfer_id: p for p in Payment.objects.filter(transfer__in=found.transfers, active=True)}
        for transfer in found.transfers:
            transfer.paid = paid.get(transfer.pk)
        found.payments = list(
            Payment.objects.filter(night=night).select_related("payer", "payee", "recorded_by")
        )
    return found
