"""Read-only views of finalized sets and of a session's settle-up."""

from dataclasses import dataclass, field

from games import clock
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
    play_seconds: object = None
    join_order: int = 0
    rake_total: int = 0

    @property
    def settlement_balance(self):
        return self.net + self.rake_total

    @property
    def pk(self):
        return self.member.pk


@dataclass
class NightOutcome:
    """A session's results over its sets, and its transfers once it is closed."""

    standings: list
    plan: object = None
    transfers: list = field(default_factory=list)
    payments: list = field(default_factory=list)

    @property
    def total_to_pay(self):
        return sum(t.amount for t in self.transfers)

    @property
    def paid_amount(self):
        return sum(t.amount for t in self.transfers if t.paid)

    @property
    def still_to_pay(self):
        return self.total_to_pay - self.paid_amount

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
    rows = services.session_standings(night)
    members = Member.objects.in_bulk([row[0] for row in rows])
    found = NightOutcome(standings=[Standing(members[m], net, played, seconds) for m, net, played, seconds in rows])
    balances = dict(services.settlement_balances(night))
    for order, standing in enumerate(found.standings, 1):
        standing.join_order = order
        standing.rake_total = balances[standing.pk] - standing.net
    identities = {s.member.pk: s for s in found.standings}
    found.plan = SettlementPlan.objects.filter(night=night).first()
    if found.plan is not None:
        found.transfers = list(
            Transfer.objects.filter(plan=found.plan).select_related("payer", "payee").order_by("position")
        )
        paid = {p.transfer_id: p for p in Payment.objects.filter(transfer__in=found.transfers, active=True)}
        for transfer in found.transfers:
            transfer.paid = paid.get(transfer.pk)
            transfer.payer_token = identities[transfer.payer_id]
            transfer.payee_token = identities[transfer.payee_id]
        found.payments = list(
            Payment.objects.filter(night=night).select_related("payer", "payee", "recorded_by")
        )
    return found


def night_recap(night, standings):
    """Read-only closing recap. Buy-ins are frozen; unknown timer duration is not zero."""
    finals = list(Finalization.objects.filter(session__night=night, is_current=True)
                  .select_related("session"))
    durations = [clock.set_seconds(f.session) for f in finals]
    known = [seconds for seconds in durations if seconds is not None]
    best = max((s.net for s in standings), default=0)
    return {
        "total_buy_in": sum(f.total_buy_in for f in finals),
        "total_rake": sum(f.total_rake for f in finals),
        "all_even": all(s.net == 0 for s in standings),
        "play_seconds": sum(known) if known else None,
        "partial_time": bool(known) and len(known) != len(durations),
        "winners": [s for s in standings if s.net == best] if best > 0 else [],
    }
