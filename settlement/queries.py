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


SETTLE_LABELS = {"settled": "Settled", "partly": "Partly settled", "unsettled": "Unsettled"}


def settle_status(transfers: int, paid: int) -> str:
    """``settled``, ``partly`` or ``unsettled``, from how many transfers are marked paid.

    The one rule for the session page and for lists. A plan without transfers is settled.
    """
    if paid >= transfers:
        return "settled"
    return "partly" if paid else "unsettled"


@dataclass
class SettleState:
    """The settle-up status of one closed session. Derived from the paid marks; never stored."""

    transfers: int = 0
    paid: int = 0
    total_to_pay: int = 0
    paid_amount: int = 0

    @property
    def status(self) -> str:
        return settle_status(self.transfers, self.paid)

    @property
    def label(self) -> str:
        return SETTLE_LABELS[self.status]

    @property
    def still_to_pay(self) -> int:
        return self.total_to_pay - self.paid_amount


def settle_states(night_ids) -> dict:
    """``{night_id: SettleState}`` for these sessions, in two queries however many there are.

    Paid transfers are counted from active payments in a query of their own: a transfer
    that was paid, undone and paid again has several payment rows and still counts once.
    """
    from django.db.models import Count

    night_ids = list(night_ids)
    if not night_ids:
        return {}
    states = {night_id: SettleState() for night_id in night_ids}
    transfers = Transfer.objects.filter(plan__night_id__in=night_ids)
    for row in transfers.values("plan__night_id").annotate(count=Count("pk"), total=Sum("amount")):
        state = states[row["plan__night_id"]]
        state.transfers, state.total_to_pay = row["count"], row["total"]
    paid = Payment.objects.filter(active=True, transfer__isnull=False).values("transfer_id")
    for row in transfers.filter(pk__in=paid).values("plan__night_id").annotate(count=Count("pk"), total=Sum("amount")):
        state = states[row["plan__night_id"]]
        state.paid, state.paid_amount = row["count"], row["total"]
    return states


@dataclass
class ViewerPart:
    """What one member still pays or receives in a closed session. Derived from the paid marks; never stored."""

    transfers: list
    to_pay: int = 0  # unpaid transfers the member pays
    to_receive: int = 0  # unpaid transfers the member receives

    @property
    def kind(self) -> str:
        """``pay``, ``receive``, ``settled`` (every transfer of theirs is paid) or ``none`` (no transfer)."""
        if not self.transfers:
            return "none"
        if self.to_pay:
            return "pay"
        return "receive" if self.to_receive else "settled"

    @property
    def amount(self) -> int:
        return self.to_pay or self.to_receive


@dataclass
class NightOutcome:
    """A session's results over its sets, and its transfers once it is closed."""

    standings: list
    plan: object = None
    transfers: list = field(default_factory=list)
    payments: list = field(default_factory=list)
    results: list = field(default_factory=list)  # services.result_rows(night), kept for the recap

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
        return settle_status(len(self.transfers), self.paid_count)

    @property
    def status_label(self) -> str:
        return SETTLE_LABELS[self.status]

    def standing_for(self, member_id):
        return next((s for s in self.standings if s.member.pk == member_id), None)

    def transfers_for(self, member_id):
        return [t for t in self.transfers if member_id in (t.payer_id, t.payee_id)]

    def part_for(self, member_id) -> ViewerPart:
        mine = self.transfers_for(member_id)
        return ViewerPart(
            transfers=mine,
            to_pay=sum(t.amount for t in mine if t.payer_id == member_id and not t.paid),
            to_receive=sum(t.amount for t in mine if t.payee_id == member_id and not t.paid),
        )


def night_outcome(night) -> NightOutcome:
    results = services.result_rows(night)
    rows = services.session_standings(night, results)
    members = Member.objects.in_bulk([row[0] for row in rows])
    found = NightOutcome(standings=[Standing(members[m], net, played, seconds) for m, net, played, seconds in rows])
    found.results = results
    balances = dict(services.settlement_balances(night, results))
    for order, standing in enumerate(found.standings, 1):
        standing.join_order = order
        standing.rake_total = balances[standing.pk] - standing.net
    identities = {s.member.pk: s for s in found.standings}
    found.plan = SettlementPlan.objects.filter(night=night).first()
    if found.plan is not None:
        found.transfers = list(
            Transfer.objects.filter(plan=found.plan).select_related("payer", "payee").order_by("position")
        )
        found.payments = list(
            Payment.objects.filter(night=night).select_related("payer", "payee", "recorded_by")
        )
        # A transfer's payment is recorded under the transfer's own session (services.mark_paid),
        # so the session's payments hold every active one.
        paid = {p.transfer_id: p for p in found.payments if p.active and p.transfer_id is not None}
        for transfer in found.transfers:
            transfer.paid = paid.get(transfer.pk)
            transfer.payer_token = identities[transfer.payer_id]
            transfer.payee_token = identities[transfer.payee_id]
    return found


@dataclass
class RecapLine:
    """One player's session over its finalized sets, from their frozen results."""

    standing: Standing
    buy_in: int = 0
    cash_out: int = 0  # cash-outs plus any share of a host override
    buy_ins: int = 0
    place: int = 0  # tied results share a place
    share: int = 0  # whole percent of the largest result of the session, win or loss
    sets: list = field(default_factory=list)  # [(set_number, net)]

    @property
    def member(self):
        return self.standing.member

    @property
    def net(self):
        return self.standing.net

    @property
    def play_seconds(self):
        return self.standing.play_seconds


@dataclass
class RecapSet:
    """One finalized set of the session."""

    number: int
    session_id: int
    players: int
    total_buy_in: int
    seconds: object = None  # None when the set has no recorded time
    winners: list = field(default_factory=list)  # [(Standing, net)] at the set's highest positive result


@dataclass
class Highlight:
    """A fact about play worth saying out loud. Never a loss; absent when it has nothing to say."""

    kind: str  # buy_ins | set_win | longest
    entries: list  # [(Standing, set_number or None)], everyone tied
    count: object = None
    amount: object = None
    seconds: object = None


@dataclass
class Recap:
    total_buy_in: int
    total_rake: int
    all_even: bool
    play_seconds: object  # None when no finalized set has a recorded time
    partial_time: bool
    winners: list
    players: int = 0
    set_count: int = 0
    buy_ins: int = 0
    ranking: list = field(default_factory=list)
    sets: list = field(default_factory=list)
    highlights: list = field(default_factory=list)
    mine: object = None  # the viewer's RecapLine, when they played


def _highlights(lines, rows, by_member, set_count) -> list:
    found = []
    most = max((line.buy_ins for line in lines), default=0)
    if any(line.buy_ins != most for line in lines):
        found.append(Highlight("buy_ins", [(line.standing, None) for line in lines if line.buy_ins == most], count=most))
    best = max((row.net for row in rows), default=0)
    if set_count > 1 and best > 0:
        entries = [(by_member[row.member_id].standing, row.set_number) for row in rows if row.net == best]
        found.append(Highlight("set_win", entries, amount=best))
    timed = [line for line in lines if line.play_seconds is not None]
    longest = max((line.play_seconds for line in timed), default=0)
    if len(timed) > 1 and any(line.play_seconds != longest for line in timed):
        entries = [(line.standing, None) for line in timed if line.play_seconds == longest]
        found.append(Highlight("longest", entries, seconds=longest))
    return found


def night_recap(night, standings, seconds=None, *, results=None, viewer_id=None) -> Recap:
    """Read-only closing recap. Figures are frozen results; unknown timer duration is not zero.

    ``seconds`` is ``{session_id: seconds}`` for the session's timed sets and ``results`` is
    ``services.result_rows(night)``, when the caller has them.
    """
    finals = list(Finalization.objects.filter(session__night=night, is_current=True))
    timed = clock.seconds_by_set([f.session_id for f in finals]) if seconds is None else seconds
    rows = services.result_rows(night) if results is None else results
    durations = [timed.get(f.session_id) for f in finals]
    known = [seconds for seconds in durations if seconds is not None]
    best = max((s.net for s in standings), default=0)

    by_member = {s.pk: RecapLine(s) for s in standings}
    by_set = {}
    for row in rows:
        line = by_member[row.member_id]
        line.buy_in += row.buy_in_total
        line.cash_out += row.cash_out
        line.buy_ins += row.buy_in_count
        line.sets.append((row.set_number, row.net))
        by_set.setdefault(row.session_id, []).append(row)
    largest = max((abs(s.net) for s in standings), default=0)
    ranking = sorted(by_member.values(), key=lambda line: (-line.net, line.member.display_name.lower(), line.member.pk))
    for position, line in enumerate(ranking, 1):
        tied = position > 1 and ranking[position - 2].net == line.net
        line.place = ranking[position - 2].place if tied else position
        line.share = abs(line.net) * 100 // largest if largest else 0

    sets = []
    for final in finals:
        played = by_set.get(final.session_id, [])
        top = max((row.net for row in played), default=0)
        sets.append(RecapSet(
            number=played[0].set_number if played else 0, session_id=final.session_id, players=len(played),
            total_buy_in=final.total_buy_in, seconds=timed.get(final.session_id),
            winners=[(by_member[row.member_id].standing, row.net) for row in played if row.net == top] if top > 0 else [],
        ))
    sets.sort(key=lambda one: one.number)

    return Recap(
        total_buy_in=sum(f.total_buy_in for f in finals),
        total_rake=sum(f.total_rake for f in finals),
        all_even=all(s.net == 0 for s in standings),
        play_seconds=sum(known) if known else None,
        partial_time=bool(known) and len(known) != len(durations),
        winners=[s for s in standings if s.net == best] if best > 0 else [],
        players=len(standings),
        set_count=len(finals),
        buy_ins=sum(line.buy_ins for line in ranking),
        ranking=ranking,
        sets=sets,
        highlights=_highlights(ranking, rows, by_member, len(finals)),
        mine=by_member.get(viewer_id),
    )


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


def roster_activity(member_ids) -> dict:
    """``{member_id: (sessions played, date of the latest)}`` for the roster, in one query.

    A session counts as it does in ``group_stats``, once whatever its unit. A member who
    never played a counted session is absent.
    """
    from django.db.models import Count, Max

    if not member_ids:
        return {}
    rows = counted_results().filter(member_id__in=member_ids).values("member_id").annotate(
        sessions=Count("finalization__session__night_id", distinct=True),
        last=Max("finalization__session__night__game_date"),
    )
    return {row["member_id"]: (row["sessions"], row["last"]) for row in rows}


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
