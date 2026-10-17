"""The group page's Sessions tab: table cards for the sessions in progress, then the viewer's past nights.

Read-only and batched: the number of queries does not grow with the number of sessions.
"""
import datetime
from dataclasses import dataclass, field

from django.urls import reverse
from django.utils import timezone

from games import clock
from games.models import GameSession, Participant
from settlement import queries as settlement_queries

State = GameSession.State
CHIPS = 6  # seated players shown as chips on a card; the rest are "+N"


def _destination(card) -> tuple[str, str]:
    """Where a card leads and what its button says: the set while it is unfinished, else the session."""
    s = card.latest_set
    if s.state == State.RUNNING:
        return reverse("session", args=[s.pk]), "Open the table"
    if s.state in (State.SETUP, State.OPEN, State.RECONCILIATION):
        return reverse("session", args=[s.pk]), f"Open set {s.set_number}"
    return reverse("night", args=[card.pk]), "Go to the session"


def _band(card) -> int:
    """Where a card goes: tables in play first, the viewer's own before others in each, drafts last."""
    state = card.latest_set.state
    if state == State.SETUP:
        return 4
    playing = 0 if state == State.RUNNING else 2
    return playing if card.mine else playing + 1


def current_cards(me, nights) -> list:
    """The open sessions with something this member may see, as cards in the order the tab shows them."""
    cards = [n for n in nights if not n.is_closed and n.shown_sets]
    set_ids = [c.latest_set.pk for c in cards]
    seated = {}
    for p in (
        Participant.objects.filter(session_id__in=set_ids, status=Participant.Status.JOINED)
        .select_related("member").order_by("session_id", "join_order")
    ):
        seated.setdefault(p.session_id, []).append(p)
    playing = [c.latest_set.pk for c in cards if c.latest_set.state == State.RUNNING]
    seconds = clock.seconds_by_set(playing) if playing else {}
    today = timezone.localdate()
    for card in cards:
        card.seated = seated.get(card.latest_set.pk, [])
        card.at_table = len(card.seated)
        card.mine = any(p.member_id == me.pk for p in card.seated)
        card.seconds = seconds.get(card.latest_set.pk)
        card.is_today = card.game_date == today
        card.chips, card.more_seated = card.seated[:CHIPS], max(card.at_table - CHIPS, 0)
        card.url, card.action_label = _destination(card)
    return sorted(cards, key=lambda c: (_band(c), c.game_date, c.pk))


@dataclass
class Debt:
    """A transfer of a past session that the viewer still pays (``i_pay``) or receives."""

    other: object
    i_pay: bool
    amount: int


@dataclass
class Month:
    first_day: datetime.date
    nights: list = field(default_factory=list)


@dataclass
class Year:
    year: int
    open: bool = False
    months: list = field(default_factory=list)

    @property
    def count(self) -> int:
        return sum(len(month.nights) for month in self.months)


def past_years(me, nights) -> list:
    """The closed sessions, newest first, by month inside years, with the viewer's net and debts.

    The current year is open; earlier years are closed. With nothing this year, the newest year is open.
    """
    nights = sorted((n for n in nights if n.is_closed and n.shown_sets), key=lambda n: (n.game_date, n.pk), reverse=True)
    if not nights:
        return []
    ids = [n.pk for n in nights]
    states = settlement_queries.settle_states(ids)
    nets = settlement_queries.session_nets(ids, [me.pk])
    debts = {}
    for t in settlement_queries.unpaid_transfers([me.pk]):
        i_pay = t.payer_id == me.pk
        debts.setdefault(t.plan.night_id, []).append(Debt(t.payee if i_pay else t.payer, i_pay, t.amount))
    years = []
    for night in nights:
        night.settle, night.my_net, night.debts = states[night.pk], nets.get((night.pk, me.pk)), debts.get(night.pk, [])
        if not years or years[-1].year != night.game_date.year:
            years.append(Year(night.game_date.year))
        months = years[-1].months
        first_day = night.game_date.replace(day=1)
        if not months or months[-1].first_day != first_day:
            months.append(Month(first_day))
        months[-1].nights.append(night)
    this_year = timezone.localdate().year
    for year in years:
        year.open = year.year == this_year
    if not any(year.open for year in years):
        years[0].open = True
    return years


def sessions_context(me) -> dict:
    from web.views import visible_nights

    nights = list(visible_nights(me))
    years = past_years(me, nights)
    return {
        "cards": current_cards(me, nights),
        "past_years": years,
        "not_settled": sum(1 for y in years for m in y.months for n in m.nights if n.settle.status != "settled"),
    }
