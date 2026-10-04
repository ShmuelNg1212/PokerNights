"""Read-only views of finalized sets and of a session's settle-up."""

import datetime
from dataclasses import dataclass, field

from django.db.models import Sum

from games import clock
from games.models import GameNight, GameSession
from groups.models import Member
from ledger.models import Finalization, PlayerResult

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


@dataclass
class PlayerStats:
    """One player's record over closed sessions, in one unit."""

    member: Member
    net: int = 0
    sessions: int = 0
    wins: int = 0

    @property
    def pk(self):
        return self.member.pk

    @property
    def win_percent(self) -> int:
        """Whole percent of sessions that ended in profit, rounded down."""
        return self.wins * 100 // self.sessions if self.sessions else 0


def counted_results():
    """Frozen results that count for statistics: current results of finalized sets in closed sessions."""
    return PlayerResult.objects.filter(
        is_current=True, finalization__is_current=True,
        finalization__session__state=GameSession.State.FINALIZED,
        finalization__session__night__status=GameNight.Status.CLOSED,
        finalization__session__night__archived_at__isnull=True,
    )


def stat_results(group):
    return counted_results().filter(group=group)


def stat_periods(group) -> dict:
    """``{unit: [first day of each month with a closed session, newest first]}``. Units never mix."""
    found = {}
    rows = stat_results(group).values_list("unit", "finalization__session__night__game_date").distinct()
    for unit, game_date in rows:
        found.setdefault(unit, set()).add(game_date.replace(day=1))
    return {unit: sorted(months, reverse=True) for unit, months in found.items()}


def group_stats(group, unit, month: datetime.date | None = None) -> list:
    """Players ranked by profit or loss over closed sessions in one unit.

    A player's sets are added up per session first, so a session counts once and is won
    when its total is above zero. ``net`` is the frozen result after rake, not a
    settle-up balance. ``month`` is any date in the wanted month of the session date.
    """
    rows = stat_results(group).filter(unit=unit)
    if month is not None:
        rows = rows.filter(
            finalization__session__night__game_date__year=month.year,
            finalization__session__night__game_date__month=month.month,
        )
    per_session = rows.values("member_id", "finalization__session__night_id").annotate(total=Sum("net"))
    stats = {}
    for row in per_session:
        line = stats.setdefault(row["member_id"], PlayerStats(member=None))
        line.net += row["total"]
        line.sessions += 1
        line.wins += row["total"] > 0
    members = Member.objects.in_bulk(stats)
    for member_id, line in stats.items():
        line.member = members[member_id]
    return sorted(stats.values(), key=lambda s: (-s.net, s.member.display_name.lower(), s.pk))


def member_records(member_ids) -> dict:
    """``{member_id: {unit: PlayerStats}}`` over closed sessions, for several members in one query.

    The same rule as ``group_stats``: sets are added per session first, and units never mix.
    """
    rows = counted_results().filter(member_id__in=member_ids).values(
        "member_id", "unit", "finalization__session__night_id"
    ).annotate(total=Sum("net"))
    found = {}
    for row in rows:
        line = found.setdefault(row["member_id"], {}).setdefault(row["unit"], PlayerStats(member=None))
        line.net += row["total"]
        line.sessions += 1
        line.wins += row["total"] > 0
    return found


def unpaid_transfers(member_ids) -> list:
    """Transfers of closed sessions that these members still pay or receive, oldest session first."""
    from django.db.models import Q

    paid = Payment.objects.filter(active=True, transfer__isnull=False).values("transfer_id")
    return list(
        Transfer.objects.filter(Q(payer_id__in=member_ids) | Q(payee_id__in=member_ids))
        .filter(plan__night__archived_at__isnull=True)
        .exclude(pk__in=paid)
        .select_related("payer", "payee", "plan__night__table")
        .order_by("plan__night__game_date", "plan__night_id", "position")
    )


def session_nets(night_ids, member_ids) -> dict:
    """``{(night_id, member_id): net}`` over the finalized sets of these sessions."""
    rows = PlayerResult.objects.filter(
        is_current=True, member_id__in=member_ids, finalization__session__night_id__in=night_ids,
    ).values("member_id", "finalization__session__night_id").annotate(total=Sum("net"))
    return {(row["finalization__session__night_id"], row["member_id"]): row["total"] for row in rows}


def night_has_records(night) -> bool:
    """True when the session has a settle-up plan or a payment record."""
    return SettlementPlan.objects.filter(night=night).exists() or Payment.objects.filter(night=night).exists()


def unpaid_in(night) -> list:
    """The transfers of this session that nobody has marked paid."""
    paid = Payment.objects.filter(active=True, transfer__isnull=False).values("transfer_id")
    return list(Transfer.objects.filter(plan__night=night).exclude(pk__in=paid).select_related("payer", "payee").order_by("position"))
