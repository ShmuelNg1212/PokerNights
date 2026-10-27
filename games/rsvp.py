"""RSVP for a session: the only code allowed to announce one and to write answers.

A host announces a session (``GameNight``). Members answer In or Out. An In takes a
seat while the session has one under its seat limit, else it waits in line. When a
seat opens, the first in line takes it and is told. Each write locks the session row.
"""

from dataclasses import dataclass, field

from django.db import transaction
from django.db.models import F
from django.urls import reverse
from django.utils import timezone

from audit import services as audit
from groups.access import NotAllowed, require_host
from groups.errors import RuleError
from groups.models import Member
from notify import services as notify

from .models import GameNight, GameSession, Rsvp
from .services import UNFINISHED_STATES, lock_night

Status = Rsvp.Status
State = GameSession.State

MIN_SEATS, MAX_SEATS = 2, 12
# Answers count while set 1 is prepared. Once it is in play, the host adds players to the set.
ANSWER_STATES = (State.SETUP, State.OPEN)


def _set_one(night) -> GameSession:
    return night.sets.order_by("set_number").first()


def _changed(night) -> None:
    # Open pages poll their set's version: bump every set so they show the change.
    GameSession.objects.filter(night=night).update(version=F("version") + 1)


def _clean_limit(value) -> int:
    if type(value) is not int or not MIN_SEATS <= value <= MAX_SEATS:
        raise RuleError(f"Seats must be between {MIN_SEATS} and {MAX_SEATS}.")
    return value


def answering_open(night, first=None) -> bool:
    """True while players can answer: announced, open, not archived, set 1 not yet in play."""
    first = first or _set_one(night)
    return (
        night.announced_at is not None and not night.is_closed and not night.is_archived
        and first is not None and first.state in ANSWER_STATES
    )


def _require_open(night) -> GameSession:
    first = _set_one(night)
    if night.announced_at is None:
        raise RuleError("This session is not announced yet.")
    if not answering_open(night, first):
        raise RuleError("Answers are closed: play has started. Ask a host to add you to the set.")
    return first


def confirmed_count(night) -> int:
    return night.rsvps.filter(status=Status.CONFIRMED).count()


def waitlist(night) -> list:
    return list(night.rsvps.filter(status=Status.WAITLISTED).select_related("member").order_by("queued_at", "id"))


def _when(night) -> str:
    when = f"{night.game_date:%a, %b %-d}"
    if night.start_time:
        when += f", {night.start_time:%-I:%M %p}"
    return when


def _url(night) -> str:
    return reverse("night", args=[night.pk])


def _seat(night, row, actor_user, first) -> None:
    """Move one waiting row into a seat and tell its member."""
    row.status = Status.CONFIRMED
    row.save(update_fields=["status", "updated_at"])
    audit.record(
        "rsvp.seated", actor=actor_user, group_id=night.group_id, session_id=first.pk, target=row,
        summary=f"{row.member.display_name} moved up from the waitlist",
    )
    if row.member.user_id and row.member.user_id != actor_user.pk:
        notify.tell_night(
            [row.member.user_id], group_id=night.group_id, night_id=night.pk, session_id=first.pk, kind="seated",
            title=f"{night.table.name} · {_when(night)}", body="A seat opened. You're in.", url=_url(night),
            actor_name="",
        )


def _fill(night, actor_user, first) -> None:
    """Seat the line in order while there are free seats."""
    free = night.seat_limit - confirmed_count(night)
    for row in waitlist(night)[:max(free, 0)]:
        _seat(night, row, actor_user, first)


@transaction.atomic
def announce(night_id, actor: Member, *, start_time=None, seat_limit=None) -> GameNight:
    """Make a draft session visible to players and tell each member with a login. A repeated tap changes nothing."""
    require_host(actor)
    night = lock_night(night_id, actor.group_id)
    if night.announced_at is not None:
        return night
    first = _set_one(night)
    if night.is_closed or first is None or first.state not in ANSWER_STATES:
        raise RuleError("Play has started. Add players to the set instead.")
    night.seat_limit = _clean_limit(night.table.seat_count if seat_limit is None else seat_limit)
    night.start_time = start_time
    night.announced_at = timezone.now()
    night.save(update_fields=["seat_limit", "start_time", "announced_at"])
    audit.record(
        "night.announced", actor=actor.user, group_id=night.group_id, session_id=first.pk, target=night,
        summary=f"Announced {night} with {night.seat_limit} seats",
    )
    users = Member.objects.filter(
        group_id=night.group_id, status=Member.Status.ACTIVE, user__isnull=False
    ).exclude(user_id=actor.user_id).values_list("user_id", flat=True)
    notify.tell_night(
        list(users), group_id=night.group_id, night_id=night.pk, session_id=first.pk, kind="announced",
        title=f"{night.table.name} · {_when(night)}", body=f"{actor.display_name} is getting a game together. Are you in?",
        url=_url(night), actor_name=actor.display_name,
    )
    _changed(night)
    return night


@transaction.atomic
def answer(night_id, actor: Member, member_id, going: bool, request_id) -> Rsvp:
    """Record In or Out for ``member_id``. A player answers for themselves; a host for anyone on the roster."""
    if str(member_id) != str(actor.pk):
        require_host(actor)
    night = lock_night(night_id, actor.group_id)
    first = _require_open(night)
    if request_id is not None:
        done = Rsvp.objects.filter(request_id=request_id, night=night).first()
        if done is not None:
            return done  # the same tap sent twice
    member = Member.objects.filter(group_id=night.group_id, pk=member_id, status=Member.Status.ACTIVE).first()
    if member is None:
        raise RuleError("That player is not in this group.")
    row = Rsvp.objects.filter(night=night, member=member).first()
    was = row.status if row else None
    if going and was in (Status.CONFIRMED, Status.WAITLISTED):
        return row
    if not going and was == Status.OUT:
        return row
    now = timezone.now()
    if going:
        status = Status.CONFIRMED if confirmed_count(night) < night.seat_limit else Status.WAITLISTED
    else:
        status = Status.OUT
    if row is None:
        row = Rsvp(night=night, member=member, queued_at=now)
    if going:
        row.queued_at = now  # a new In goes to the end of the line
    row.status, row.answered_by, row.request_id = status, actor.user, request_id
    row.save()
    by = "" if member.pk == actor.pk else f" (answered by {actor.display_name})"
    words = {Status.CONFIRMED: "is coming", Status.WAITLISTED: "joined the waitlist", Status.OUT: "can't make it"}
    audit.record(
        "rsvp.answered", actor=actor.user, group_id=night.group_id, session_id=first.pk, target=row,
        summary=f"{member.display_name} {words[status]}{by}",
    )
    if was == Status.CONFIRMED:
        _fill(night, actor.user, first)
    _changed(night)
    return row


@transaction.atomic
def set_seat_limit(night_id, actor: Member, limit) -> GameNight:
    """Change how many players the session confirms. Raising it seats the line in order."""
    require_host(actor)
    night = lock_night(night_id, actor.group_id)
    first = _require_open(night)
    limit = _clean_limit(limit)
    coming = confirmed_count(night)
    if limit < coming:
        raise RuleError(f"{coming} players are coming. Mark someone out first.")
    if limit == night.seat_limit:
        return night
    night.seat_limit = limit
    night.save(update_fields=["seat_limit"])
    audit.record(
        "night.seats", actor=actor.user, group_id=night.group_id, session_id=first.pk, target=night,
        summary=f"Set the seats of {night} to {limit}",
    )
    _fill(night, actor.user, first)
    _changed(night)
    return night


@transaction.atomic
def seat_from_waitlist(night_id, actor: Member, member_id) -> Rsvp:
    """A host seats one waiting player now. The limit grows to make room."""
    require_host(actor)
    night = lock_night(night_id, actor.group_id)
    first = _require_open(night)
    row = night.rsvps.select_related("member").filter(member_id=member_id, status=Status.WAITLISTED).first()
    if row is None:
        raise RuleError("That player is not on the waitlist.")
    coming = confirmed_count(night) + 1
    if coming > MAX_SEATS:
        raise RuleError(f"A session has {MAX_SEATS} seats at most.")
    night.seat_limit = max(night.seat_limit, coming)
    night.save(update_fields=["seat_limit"])
    _seat(night, row, actor.user, first)
    _changed(night)
    return row


def member_removed(member, actor_user) -> None:
    """A member left the group: each of their answers for a session still taking answers turns Out.

    Called inside the removal's transaction (``groups.services.REMOVED_HOOKS``).
    """
    rows = Rsvp.objects.filter(
        member=member, status__in=(Status.CONFIRMED, Status.WAITLISTED),
        night__sets__set_number=1, night__sets__state__in=UNFINISHED_STATES,
    ).values_list("night_id", flat=True)
    for night_id in set(rows):
        night = lock_night(night_id, member.group_id, allow_archived=True)
        row = night.rsvps.get(member=member)
        was = row.status
        row.status, row.answered_by, row.request_id = Status.OUT, actor_user, None
        row.save()
        first = _set_one(night)
        audit.record(
            "rsvp.answered", actor=actor_user, group_id=night.group_id, session_id=first.pk, target=row,
            summary=f"{member.display_name} left the group, so can't make it",
        )
        if was == Status.CONFIRMED and answering_open(night, first):
            _fill(night, actor_user, first)
        _changed(night)


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
    for row in Rsvp.objects.filter(night_id__in=found).select_related("member").order_by("queued_at", "id"):
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
    """``{member_id: (status, place in line or None)}`` for set 1 of an announced session; else empty."""
    if session.set_number != 1 or session.night.announced_at is None:
        return {}
    found, place = {}, 0
    for member_id, status in session.night.rsvps.order_by("queued_at", "id").values_list("member_id", "status"):
        if status == Status.WAITLISTED:
            place += 1
        found[member_id] = (status, place if status == Status.WAITLISTED else None)
    return found
