"""The Your groups page: one card per group that reports its state. Read-only.

Every figure comes from batched queries over the viewer's active memberships, so
the number of queries does not grow with groups or players.
"""

from dataclasses import dataclass, field

from django.db.models import Count, OuterRef, Subquery
from django.urls import reverse

from games import clock
from games.models import GameNight, GameSession, Participant, Table
from groups.models import Member
from settlement import queries as settlement_queries

State = GameSession.State
TOKENS_SHOWN = 6
DUES_SHOWN = 3
# Where a card sorts: a set in play first, then an open session, then the quiet groups.
ORDER = {"play": 0, "open": 1, "quiet": 2}


@dataclass
class Due:
    """One unpaid transfer, from the viewer's side."""

    owes: bool  # True: the viewer pays; False: the viewer is paid
    other: Member
    amount: int
    unit: str
    night: GameNight


@dataclass
class Card:
    me: Member
    members: list = field(default_factory=list)
    kind: str = "quiet"  # play, open or quiet
    night: GameNight = None
    set: GameSession = None
    more_open: int = 0
    action_label: str = ""
    action_url: str = ""
    action_primary: bool = False
    at_table: int = 0
    seconds: object = None
    records: list = field(default_factory=list)  # [(unit, PlayerStats)]
    dues: list = field(default_factory=list)
    more_dues: int = 0
    last_night: GameNight = None
    last_net: object = None

    @property
    def group(self):
        return self.me.group

    @property
    def tokens(self):
        return self.members[:TOKENS_SHOWN]

    @property
    def more_members(self):
        return max(0, len(self.members) - TOKENS_SHOWN)

    @property
    def has_stats(self):
        return self.last_night is not None


def home_cards(user) -> list:
    memberships = list(
        Member.objects.filter(user=user, status=Member.Status.ACTIVE, group__archived_at__isnull=True)
        .select_related("group").order_by("group__name")
    )
    if not memberships:
        return []
    cards = {m.group_id: Card(me=m) for m in memberships}
    group_ids, my_ids = list(cards), [m.pk for m in memberships]

    for member in Member.objects.filter(group_id__in=group_ids, status=Member.Status.ACTIVE):
        cards[member.group_id].members.append(member)

    with_table = set(Table.objects.filter(group_id__in=group_ids, archived_at__isnull=True).values_list("group_id", flat=True))
    open_nights = (
        GameNight.objects.filter(group_id__in=group_ids, status=GameNight.Status.OPEN, archived_at__isnull=True)
        .select_related("table").prefetch_related("sets").order_by("-game_date", "-pk")
    )
    by_group = {}
    for night in open_nights:
        card = cards[night.group_id]
        sets = sorted(night.sets.all(), key=lambda s: s.set_number)
        # Drafts are for hosts only, as on the group page.
        night.shown_sets = [s for s in sets if card.me.is_host or s.state != State.SETUP]
        if night.shown_sets:
            night.latest_set = night.shown_sets[-1]
            by_group.setdefault(night.group_id, []).append(night)
    for group_id, card in cards.items():
        _choose_status(card, by_group.get(group_id, []), group_id in with_table)

    playing = [card.set.pk for card in cards.values() if card.kind == "play"]
    if playing:
        seconds = clock.seconds_by_set(playing)
        seated = dict(
            Participant.objects.filter(session_id__in=playing, status=Participant.Status.JOINED)
            .values_list("session_id").annotate(Count("pk"))
        )
        for card in cards.values():
            if card.kind == "play":
                card.seconds, card.at_table = seconds.get(card.set.pk), seated.get(card.set.pk, 0)

    records = settlement_queries.member_records(my_ids)
    for card in cards.values():
        mine = records.get(card.me.pk, {})
        card.records = [(unit, mine[unit]) for unit in ("php", "chips") if unit in mine]

    for transfer in settlement_queries.unpaid_transfers(my_ids):
        night = transfer.plan.night
        card = cards[night.group_id]
        owes = transfer.payer_id == card.me.pk
        if len(card.dues) < DUES_SHOWN:
            card.dues.append(Due(owes, transfer.payee if owes else transfer.payer, transfer.amount, night.unit, night))
        else:
            card.more_dues += 1

    last = Subquery(
        GameNight.objects.filter(group_id=OuterRef("group_id"), status=GameNight.Status.CLOSED, archived_at__isnull=True)
        .order_by("-game_date", "-pk").values("pk")[:1]
    )
    last_nights = list(
        GameNight.objects.filter(group_id__in=group_ids, status=GameNight.Status.CLOSED, pk=last).select_related("table")
    )
    nets = settlement_queries.session_nets([n.pk for n in last_nights], my_ids) if last_nights else {}
    for night in last_nights:
        card = cards[night.group_id]
        card.last_night, card.last_net = night, nets.get((night.pk, card.me.pk))

    return sorted(cards.values(), key=lambda c: (ORDER[c.kind], c.group.name.lower(), c.group.pk))


def _choose_status(card, nights, has_table) -> None:
    """One status and one action per card, for this viewer."""
    group_url = reverse("group", args=[card.me.group_id])
    if not nights:
        if card.me.is_host:
            card.action_primary = True
            if has_table:
                card.action_label, card.action_url = "New session", reverse("session_create", args=[card.me.group_id])
            else:
                card.action_label, card.action_url = "Add a table", f"{group_url}?view=settings#tables"
        return
    running = [n for n in nights if n.latest_set.state == State.RUNNING]
    card.night = (running or nights)[0]
    card.set = card.night.latest_set
    card.more_open = len(nights) - 1
    set_url = reverse("session", args=[card.set.pk])
    if running:
        card.kind = "play"
        card.action_label, card.action_url, card.action_primary = "Open the table", set_url, True
        return
    card.kind = "open"
    if card.set.state in (State.SETUP, State.OPEN, State.RECONCILIATION):
        card.action_label, card.action_url = f"Open set {card.set.set_number}", set_url
        # A host has work to do in these states; a player can join an open set.
        card.action_primary = card.me.is_host or card.set.state == State.OPEN
    else:
        card.action_label, card.action_url = "Go to the session", reverse("night", args=[card.night.pk])
        card.action_primary = card.me.is_host


def archived_groups(user) -> list:
    """The viewer's host memberships in archived groups: only a host can restore one."""
    return list(
        Member.objects.filter(user=user, status=Member.Status.ACTIVE, role=Member.Role.HOST, group__archived_at__isnull=False)
        .select_related("group", "group__archived_by").order_by("group__name")
    )
