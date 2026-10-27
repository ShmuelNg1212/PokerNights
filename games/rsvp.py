"""RSVP for a session, the read side: who is coming, the waitlist, and whether answers still count.

A host announces a session (``GameNight``). Members answer In or Out. An In takes a seat while the
session has one under its seat limit, else it waits in line. The writes are in ``games.services``.
"""

from dataclasses import dataclass, field

from groups.models import Member

from .models import MAX_SEATS, MIN_SEATS, GameNight, GameSession, Rsvp  # noqa: F401 - the seat bounds are read from here

Status = Rsvp.Status
State = GameSession.State

# Answers count while set 1 is prepared. Once it is in play, the host adds players to the set.
ANSWER_STATES = (State.SETUP, State.OPEN)


def set_one(night) -> GameSession:
    return night.sets.order_by("set_number").first()


def answering_open(night, first=None) -> bool:
    """True while players can answer: announced, open, not archived, set 1 not yet in play."""
    first = first or set_one(night)
    return (
        night.announced_at is not None and not night.is_closed and not night.is_archived
        and first is not None and first.state in ANSWER_STATES
    )


def answering_nights(group_ids):
    """The announced sessions of these groups that still take answers, as a queryset."""
    return GameNight.objects.filter(
        group_id__in=group_ids, announced_at__isnull=False, status=GameNight.Status.OPEN, archived_at__isnull=True,
        sets__set_number=1, sets__state__in=ANSWER_STATES,
    )


def confirmed_count(night) -> int:
    return night.rsvps.filter(status=Status.CONFIRMED).count()


def waitlist(night) -> list:
    return list(night.rsvps.filter(status=Status.WAITLISTED).select_related("member").order_by("queued_at", "id"))


# --- Reading -------------------------------------------------------------------

@dataclass
class Board:
    """Who is coming to one announced session, for its page and its Sessions tab card."""

    night: object
    confirmed: list = field(default_factory=list)  # Rsvp rows, in the order they answered
    waitlisted: list = field(default_factory=list)  # Rsvp rows, in line order; each has .place
    out: list = field(default_factory=list)
    not_answered: list = field(default_factory=list)  # Members; filled for a host only
    mine: object = None  # the viewer's Rsvp row, or None
    open: bool = False  # answers still count

    @property
    def limit(self) -> int:
        return self.night.seat_limit

    @property
    def free(self) -> int:
        return max(self.limit - len(self.confirmed), 0)

    @property
    def full(self) -> bool:
        return self.free == 0

    @property
    def people(self) -> list:
        """Every member on this board, for the colours of their chips."""
        return [r.member for r in self.confirmed + self.waitlisted + self.out] + self.not_answered

    @property
    def chips(self) -> list:
        return [r.member for r in self.confirmed[:6]]

    @property
    def more(self) -> int:
        return max(len(self.confirmed) - 6, 0)

    @property
    def mark(self) -> tuple:
        """What another person can change here, for the polling stamps."""
        rows = sorted((r.pk, r.status, r.queued_at.isoformat()) for r in self.confirmed + self.waitlisted + self.out)
        return (self.night.announced_at.isoformat(), self.limit, str(self.night.start_time), rows)


def boards(nights, me, *, sets=None) -> dict:
    """``{night_id: Board}`` for the announced ones among ``nights``. Two queries, whatever their number.

    ``sets`` is ``{night_id: set 1}`` when the caller has the sets already; else set 1 is read per night.
    """
    nights = [n for n in nights if n.announced_at is not None]
    if not nights:
        return {}
    found = {n.pk: Board(n) for n in nights}
    answered = {}
    rows = list(Rsvp.objects.filter(night_id__in=found).select_related("member").order_by("queued_at", "id"))
    # A host who answered for someone is named as the group knows them, not by their login.
    others = {r.answered_by_id for r in rows if r.answered_by_id != r.member.user_id}
    names = dict(
        Member.objects.filter(group_id=nights[0].group_id, user_id__in=others).values_list("user_id", "display_name")
    ) if others else {}
    for row in rows:
        row.answered_by_name = names.get(row.answered_by_id, "a host") if row.answered_by_id in others else ""
        board = found[row.night_id]
        answered.setdefault(row.night_id, set()).add(row.member_id)
        {Status.CONFIRMED: board.confirmed, Status.WAITLISTED: board.waitlisted, Status.OUT: board.out}[row.status].append(row)
        if row.member_id == me.pk:
            board.mine = row
    roster = None
    if me.is_host:
        roster = list(Member.objects.filter(group_id=me.group_id, status=Member.Status.ACTIVE).order_by("display_name", "pk"))
    for board in found.values():
        for place, row in enumerate(board.waitlisted, 1):
            row.place = place
        first = (sets or {}).get(board.night.pk)
        board.open = answering_open(board.night, first)
        if roster is not None:
            seen = answered.get(board.night.pk, set())
            board.not_answered = [m for m in roster if m.pk not in seen]
    return found


def answers_for_set_one(session) -> dict:
    """``{member_id: (status, place in line or None)}`` for set 1 of an announced session; else empty.

    In answer order, so a caller that can tick only some of the confirmed ticks the first to answer.
    """
    if session.set_number != 1 or session.night.announced_at is None:
        return {}
    found, place = {}, 0
    for member_id, status in session.night.rsvps.order_by("queued_at", "id").values_list("member_id", "status"):
        if status == Status.WAITLISTED:
            place += 1
        found[member_id] = (status, place if status == Status.WAITLISTED else None)
    return found
