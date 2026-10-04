"""The only code allowed to change tables, presets, sessions and participants."""

import datetime
import uuid

from django.db import IntegrityError, transaction
from django.utils import timezone

from audit import services as audit
from groups.access import require_host
from groups.errors import RuleError
from groups.models import Member
from groups.services import clean_name

from . import clock
from .models import (
    GameNight, GameSession, GameType, Participant, ParticipantBatch, SettingsPreset, SettingsVersion, StakesFields, Table, Unit,
)


def validated_stakes(data: dict) -> dict:
    """The six stakes values from ``data``, checked. Raises RuleError with a clear message."""
    stakes = {}
    for name in StakesFields.STAKES_FIELDS:
        value = data.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise RuleError("Each blind and buy-in amount must be more than zero.")
        stakes[name] = value
    if stakes["small_blind"] > stakes["big_blind"]:
        raise RuleError("The small blind cannot be more than the big blind.")
    if not stakes["min_buy_in"] <= stakes["default_buy_in"] <= stakes["max_buy_in"]:
        raise RuleError("The usual buy-in must be between the minimum and the maximum buy-in.")
    return stakes


def _unit(value) -> str:
    value = value or Unit.PHP
    if value not in Unit.values:
        raise RuleError("Select pesos or chips.")
    return value


def _game_type(value) -> str:
    if value not in GameType.values:
        raise RuleError("Unknown game type.")
    return value


@transaction.atomic
def save_preset(actor: Member, data: dict, *, preset_id=None) -> SettingsPreset:
    """Create a preset, or update one. Sessions keep their own copy, so no session changes."""
    require_host(actor)
    fields = {
        "name": clean_name(data.get("name"), "Preset name"),
        "game_type": _game_type(data.get("game_type")),
        "unit": _unit(data.get("unit")),
        **validated_stakes(data),
    }
    try:
        with transaction.atomic():
            if preset_id is None:
                preset = SettingsPreset.objects.create(group=actor.group, **fields)
                action = "preset.created"
            else:
                preset = SettingsPreset.objects.filter(group=actor.group, pk=preset_id, archived_at__isnull=True).first()
                if preset is None:
                    raise RuleError("That preset is not in this group.")
                for name, value in fields.items():
                    setattr(preset, name, value)
                preset.save()
                action = "preset.updated"
    except IntegrityError:
        raise RuleError(f"A preset named {fields['name']} already exists.") from None
    audit.record(action, actor=actor.user, group_id=actor.group_id, target=preset, summary=f"Saved preset {preset.name}", data=preset.stakes())
    return preset


@transaction.atomic
def create_table(actor: Member, name: str, seat_count, default_preset_id=None) -> Table:
    require_host(actor)
    name = clean_name(name, "Table name")
    try:
        seat_count = int(seat_count)
    except (TypeError, ValueError):
        raise RuleError("Enter the number of seats.") from None
    if not 2 <= seat_count <= 12:
        raise RuleError("A table has 2 to 12 seats.")
    preset = None
    if default_preset_id:
        preset = SettingsPreset.objects.filter(group=actor.group, pk=default_preset_id, archived_at__isnull=True).first()
        if preset is None:
            raise RuleError("That preset is not in this group.")
    try:
        with transaction.atomic():
            table = Table.objects.create(group=actor.group, name=name, seat_count=seat_count, default_preset=preset)
    except IntegrityError:
        raise RuleError(f"A table named {name} already exists.") from None
    audit.record("table.created", actor=actor.user, group_id=actor.group_id, target=table, summary=f"Created table {name} with {seat_count} seats")
    return table


# --- Sessions ---------------------------------------------------------------

State = GameSession.State


def lock_night(night_id, group_id) -> GameNight:
    """The session row, locked for the rest of the transaction."""
    night = GameNight.objects.select_for_update().select_related("table").filter(pk=night_id, group_id=group_id).first()
    if night is None:
        raise RuleError("That session is not in this group.")
    return night


def lock_session(session_id, group_id) -> GameSession:
    """The session row, locked for the rest of the transaction. Every session write starts here."""
    session = (
        GameSession.objects.select_for_update().select_related("table", "night").filter(pk=session_id, group_id=group_id).first()
    )
    if session is None:
        raise RuleError("That game is not in this group.")
    return session


# Checks that tell whether a session has money in it. The app that holds the
# money registers one, so this app can apply its rules without importing it.
SESSION_MONEY_CHECKS = []


def has_money(session: GameSession) -> bool:
    """True while the session has an accepted buy-in or cash-out. Such a game cannot be canceled."""
    return any(check(session) for check in SESSION_MONEY_CHECKS)


def touch(session: GameSession) -> None:
    """Record that the session changed. Call once per write, with the session locked."""
    session.version += 1
    session.save(update_fields=["version"])


def current_settings(session: GameSession) -> SettingsVersion:
    return session.settings_versions.order_by("-number").first()


def _clean_date(value) -> datetime.date:
    if isinstance(value, datetime.date):
        return value
    raise RuleError("Enter the date of the game.")


@transaction.atomic
def create_session(actor: Member, data: dict) -> GameSession:
    """Create a session with its first set. The set is in setup, with settings version 1."""
    require_host(actor)
    table = Table.objects.filter(group=actor.group, pk=data.get("table_id"), archived_at__isnull=True).first()
    if table is None:
        raise RuleError("Select a table of this group.")
    preset = None
    if data.get("preset_id"):
        preset = SettingsPreset.objects.filter(group=actor.group, pk=data["preset_id"]).first()
    shared = {
        "group": actor.group,
        "table": table,
        "game_date": _clean_date(data.get("game_date")),
        "location": (data.get("location") or "").strip()[:120],
        "game_type": _game_type(data.get("game_type")),
        "unit": _unit(data.get("unit")),
        "created_by": actor.user,
    }
    night = GameNight.objects.create(**shared)
    session = GameSession.objects.create(night=night, set_number=1, seat_count=table.seat_count, **shared)
    SettingsVersion.objects.create(
        session=session, number=1, preset=preset, created_by=actor.user, **validated_stakes(data)
    )
    audit.record(
        "session.created", actor=actor.user, group_id=actor.group_id, session_id=session.pk, target=session,
        summary=f"Created a session at {table.name} for {session.game_date:%Y-%m-%d} (set 1)",
    )
    return session


@transaction.atomic
def update_settings(session_id, actor: Member, data: dict) -> SettingsVersion:
    """Add a settings version, and change the unit if the game has no money in it yet.

    Buy-ins already recorded keep their amounts.
    """
    require_host(actor)
    session = lock_session(session_id, actor.group_id)
    if session.state not in (State.SETUP, State.OPEN, State.RUNNING):
        raise RuleError("Settings cannot change after play has ended.")
    stakes = validated_stakes(data)
    unit = _unit(data.get("unit") or session.unit)
    previous = current_settings(session)
    if unit != session.unit:
        # Amounts already recorded would change meaning, so the unit is fixed once money is in.
        if has_money(session):
            raise RuleError("Buy-ins are recorded, so the unit cannot change. Reverse them first.")
        if session.night.sets.count() > 1:
            raise RuleError("This session has several sets. They all count in one unit, so it cannot change.")
        session.unit = unit
        session.save(update_fields=["unit"])
        GameNight.objects.filter(pk=session.night_id).update(unit=unit)
        audit.record(
            "session.unit_changed", actor=actor.user, group_id=actor.group_id, session_id=session.pk, target=session,
            summary=f"Changed the unit to {Unit(unit).label}",
        )
    elif previous.stakes() == stakes:
        return previous
    version = SettingsVersion.objects.create(
        session=session, number=previous.number + 1, created_by=actor.user, **stakes
    )
    audit.record(
        "session.settings_changed", actor=actor.user, group_id=actor.group_id, session_id=session.pk, target=version,
        summary=f"Changed settings (version {version.number})", data=stakes,
    )
    touch(session)
    return version


START_HOOKS = []  # hook(session, actor, request_id), before the first clock starts.

# Called when a set resumes play, inside the transaction: ``hook(session, actor)``.
RESUME_HOOKS = []

# Called when a player who had left returns to the table: ``hook(participant, actor)``.
RETURN_HOOKS = []

# action → (states it is allowed from, resulting state)
TRANSITIONS = {
    "open": ((State.SETUP,), State.OPEN),
    "close": ((State.OPEN,), State.SETUP),
    "start": ((State.OPEN,), State.RUNNING),
    "end": ((State.RUNNING,), State.RECONCILIATION),
    "resume": ((State.RECONCILIATION,), State.RUNNING),
    "cancel": ((State.SETUP, State.OPEN, State.RUNNING, State.RECONCILIATION), State.CANCELED),
}

ACTION_LABELS = {
    "open": "Opened the game for joining",
    "close": "Closed the game (back to setup)",
    "start": "Started play",
    "end": "Ended play; counting up",
    "resume": "Resumed play",
    "cancel": "Canceled the game",
}


@transaction.atomic
def transition(session_id, actor: Member, action: str, reason: str = "", *,
               request_id=None, opening_buy_ins=True) -> GameSession:
    """Move the set through its lifecycle; first start includes optional opening buy-ins.

    The start request is persisted even with no players. Replaying it never
    reapplies money or timer effects. Finalization is a separate service.
    """
    require_host(actor)
    if action not in TRANSITIONS:
        raise RuleError("Unknown action.")
    session = lock_session(session_id, actor.group_id)
    if action == "start":
        request_id = uuid.UUID(str(request_id)) if request_id is not None else uuid.uuid4()
        if session.start_request_id == request_id:
            return session
    allowed_from, target = TRANSITIONS[action]
    if session.state not in allowed_from:
        raise RuleError(f"This game is {session.get_state_display().lower()}, so that action is not available.")
    reason = (reason or "").strip()
    if action == "resume" and session.night.sets.filter(set_number__gt=session.set_number).exists():
        raise RuleError("A later set of this session has started, so this set cannot resume play.")
    if action == "close" and session.participants.filter(status=Participant.Status.JOINED).exists():
        raise RuleError("Players have joined. Remove them first, or cancel the game.")
    if action == "cancel":
        if has_money(session):
            raise RuleError("Buy-ins are recorded. Reverse them first, or finish and finalize the game.")
        if session.state != State.SETUP and not reason:
            raise RuleError("Give a reason for canceling.")
        session.cancel_reason = reason[:255]
    if action == "start":
        if opening_buy_ins:
            for hook in START_HOOKS:
                hook(session, actor, request_id)
        session.start_request_id = request_id
    now = timezone.now()
    if action == "start":
        session.started_at = session.started_at or now
        clock.start(session, now)
    elif action == "resume":
        session.ended_at = None
        for hook in RESUME_HOOKS:
            hook(session, actor)
        clock.start(session, now, resuming=True)
    elif action == "end" or (action == "cancel" and session.state == State.RUNNING):
        # One timestamp for the set and for every player still at the table.
        clock.stop(session, now)
        session.ended_at = now
    session.state = target
    session.save(update_fields=["state", "started_at", "ended_at", "cancel_reason", "start_request_id"])
    audit.record(
        f"session.{action}", actor=actor.user, group_id=actor.group_id, session_id=session.pk, target=session,
        summary=ACTION_LABELS[action], reason=reason,
    )
    touch(session)
    return session


IN_PLAY_STATES = (State.SETUP, State.OPEN, State.RUNNING)


@transaction.atomic
def start_next_set(night_id, actor: Member) -> GameSession:
    """Open the next set of a session, with the players still at the table.

    Allowed once play of the previous set has ended; its counting and cash-outs
    can still be finished. The new set copies the table, seats and latest
    settings. It copies no money: each set has its own buy-ins.
    """
    require_host(actor)
    night = lock_night(night_id, actor.group_id)
    if night.is_closed:
        raise RuleError("This session is closed. Create a new session to play again.")
    sets = list(night.sets.order_by("set_number"))
    in_play = next((s for s in sets if s.state in IN_PLAY_STATES), None)
    if in_play is not None:
        raise RuleError(
            f"Set {in_play.set_number} is still {in_play.get_state_display().lower()}. "
            "End its play before starting the next set."
        )
    played = [s for s in sets if s.state != State.CANCELED]
    previous = played[-1] if played else sets[-1]
    new = GameSession.objects.create(
        night=night, set_number=sets[-1].set_number + 1, group_id=night.group_id, table_id=night.table_id,
        game_date=night.game_date, location=night.location, game_type=night.game_type, unit=night.unit,
        seat_count=previous.seat_count, state=State.OPEN, created_by=actor.user,
    )
    SettingsVersion.objects.create(
        session=new, number=1, created_by=actor.user, **current_settings(previous).stakes()
    )
    carried = previous.participants.filter(status=Participant.Status.JOINED).order_by("join_order")
    for order, old in enumerate(carried, start=1):
        Participant.objects.create(session=new, member_id=old.member_id, join_order=order, added_by=actor.user)
    audit.record(
        "session.created", actor=actor.user, group_id=night.group_id, session_id=new.pk, target=new,
        summary=f"Started set {new.set_number} with {len(carried)} player{'' if len(carried) == 1 else 's'} "
        f"from set {previous.set_number}",
    )
    touch(new)
    return new


def mark_finalized(session: GameSession) -> None:
    """Set the finalized state. Called only by finalization, with the session locked."""
    session.state = State.FINALIZED
    session.finalized_at = timezone.now()
    session.save(update_fields=["state", "finalized_at"])
    touch(session)


# --- Participants -----------------------------------------------------------

# Checks that run before a participant is withdrawn. An app that holds a
# participant's money registers one, so a player with money cannot disappear.
PARTICIPANT_EXIT_GUARDS = []

JOINABLE_STATES = (State.OPEN, State.RUNNING)
HOST_ADD_STATES = (State.SETUP, State.OPEN, State.RUNNING)


def _seats_taken(session) -> int:
    return session.participants.filter(status=Participant.Status.JOINED).count()


@transaction.atomic
def add_participant(session_id, actor: Member, member_id) -> Participant:
    """Put a member in the session: a player joins for themselves, a host adds anyone on the roster.

    Joining twice returns the same row. The seat check runs under the session
    lock, so simultaneous joins cannot overfill the table.
    """
    session = lock_session(session_id, actor.group_id)
    is_self = str(member_id) == str(actor.pk)
    if not is_self:
        require_host(actor)
    allowed = HOST_ADD_STATES if actor.is_host else JOINABLE_STATES
    if session.state not in allowed:
        raise RuleError("This game is not open for joining.")
    member = Member.objects.filter(group_id=session.group_id, pk=member_id, status=Member.Status.ACTIVE).first()
    if member is None:
        raise RuleError("That player is not in this group.")
    participant = Participant.objects.filter(session=session, member=member).first()
    if participant is not None and participant.status == Participant.Status.JOINED:
        return participant
    if participant is not None and participant.status == Participant.Status.LEFT and not actor.is_host:
        raise RuleError("You left this game. Ask a host to add you again.")
    if _seats_taken(session) >= session.seat_count:
        raise RuleError(f"The table is full ({session.seat_count} seats).")
    if participant is None:
        participant = Participant.objects.create(
            session=session, member=member, join_order=session.participants.count() + 1, added_by=actor.user
        )
    else:
        participant.status = Participant.Status.JOINED
        participant.left_at = None
        participant.save(update_fields=["status", "left_at"])
    if session.state == State.RUNNING:
        clock.open_interval(participant, timezone.now())
    audit.record(
        "participant.joined", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=participant,
        summary=f"{member.display_name} joined" if is_self else f"Added {member.display_name}",
    )
    touch(session)
    return participant


def _names(members) -> str:
    names = [member.display_name for member in members]
    return names[0] if len(names) == 1 else f"{', '.join(names[:-1])} and {names[-1]}"


@transaction.atomic
def add_participants(session_id, actor: Member, member_ids, request_id) -> list:
    """A host adds several members to the session in one action: all of them, or nobody.

    Everything is checked again here, under the session lock, whatever the
    screen showed. Sending the same ``request_id`` again adds nobody twice and
    returns the players of the first call. Like the single add, this only puts
    players in the game: it records no buy-in, payment or seat.
    """
    require_host(actor)
    session = lock_session(session_id, actor.group_id)
    repeated = ParticipantBatch.objects.filter(session=session, request_id=request_id).first()
    if repeated is not None:
        return list(repeated.participants.select_related("member").order_by("join_order"))
    if session.state not in HOST_ADD_STATES:
        raise RuleError("Players cannot be added at this stage of the game.")

    wanted = []
    for member_id in member_ids:
        try:
            member_id = int(member_id)
        except (TypeError, ValueError):
            raise RuleError("That selection is not valid. Select the players again.") from None
        if member_id not in wanted:
            wanted.append(member_id)
    if not wanted:
        raise RuleError("Select at least one player.")

    found = Member.objects.filter(group_id=session.group_id, pk__in=wanted, status=Member.Status.ACTIVE).in_bulk()
    if len(found) != len(wanted):
        raise RuleError("A selected player is no longer in this group. Nothing was added. Review your selection.")
    members = [found[member_id] for member_id in wanted]

    existing = {p.member_id: p for p in Participant.objects.filter(session=session, member__in=members)}
    at_table = [m for m in members if m.pk in existing and existing[m.pk].status == Participant.Status.JOINED]
    if at_table:
        verb = "is" if len(at_table) == 1 else "are"
        raise RuleError(f"{_names(at_table)} {verb} already at the table. Nothing was added. Review your selection.")

    free = session.seat_count - _seats_taken(session)
    if len(members) > free:
        over = len(members) - free
        seats = "No seat is free" if free == 0 else f"Only {free} seat{' is' if free == 1 else 's are'} free"
        raise RuleError(
            f"{seats} and you selected {len(members)} players. "
            f"Remove {over} player{'' if over == 1 else 's'}. Nothing was added."
        )

    next_order = session.participants.count() + 1
    added = []
    now = timezone.now()
    for member in members:
        participant = existing.get(member.pk)
        if participant is None:
            participant = Participant.objects.create(
                session=session, member=member, join_order=next_order, added_by=actor.user
            )
            next_order += 1
        else:
            participant.status = Participant.Status.JOINED
            participant.left_at = None
            participant.save(update_fields=["status", "left_at"])
        if session.state == State.RUNNING:
            clock.open_interval(participant, now)
        audit.record(
            "participant.joined", actor=actor.user, group_id=session.group_id, session_id=session.pk,
            target=participant, summary=f"Added {member.display_name}",
        )
        added.append(participant)
    batch = ParticipantBatch.objects.create(session=session, request_id=request_id, added_by=actor.user)
    batch.participants.set(added)
    touch(session)
    return added


def _participant(session, participant_id) -> Participant:
    participant = Participant.objects.select_related("member").filter(session=session, pk=participant_id).first()
    if participant is None:
        raise RuleError("That player is not in this game.")
    return participant


@transaction.atomic
def withdraw_participant(session_id, actor: Member, participant_id) -> Participant:
    """Take a player out of the session. Refused once the player has money in it."""
    session = lock_session(session_id, actor.group_id)
    participant = _participant(session, participant_id)
    if participant.member_id != actor.pk:
        require_host(actor)
    allowed = HOST_ADD_STATES if actor.is_host else JOINABLE_STATES
    if session.state not in allowed:
        raise RuleError("Players cannot be removed at this stage.")
    if participant.status == Participant.Status.WITHDRAWN:
        return participant
    for guard in PARTICIPANT_EXIT_GUARDS:
        guard(participant)
    participant.status = Participant.Status.WITHDRAWN
    participant.save(update_fields=["status"])
    clock.close_interval(participant, timezone.now())
    audit.record(
        "participant.withdrawn", actor=actor.user, group_id=session.group_id, session_id=session.pk,
        target=participant, summary=f"{participant.member.display_name} was taken out of the game",
    )
    touch(session)
    return participant


@transaction.atomic
def set_left(session_id, actor: Member, participant_id, left: bool = True) -> Participant:
    """Mark a player as gone for the night (their seat is free), or as back at the table."""
    require_host(actor)
    session = lock_session(session_id, actor.group_id)
    if session.state not in (State.RUNNING, State.RECONCILIATION):
        raise RuleError("Players can be marked as left only during the game.")
    participant = _participant(session, participant_id)
    wanted = Participant.Status.LEFT if left else Participant.Status.JOINED
    if participant.status == wanted:
        return participant
    if participant.status == Participant.Status.WITHDRAWN:
        raise RuleError("That player is not in this game.")
    if not left and _seats_taken(session) >= session.seat_count:
        raise RuleError(f"The table is full ({session.seat_count} seats).")
    now = timezone.now()
    participant.status = wanted
    participant.left_at = now if left else None
    participant.save(update_fields=["status", "left_at"])
    if left:
        clock.close_interval(participant, now)
    else:
        for hook in RETURN_HOOKS:
            hook(participant, actor)
        if session.state == State.RUNNING:
            clock.open_interval(participant, now)
    audit.record(
        "participant.left" if left else "participant.returned", actor=actor.user, group_id=session.group_id,
        session_id=session.pk, target=participant,
        summary=f"{participant.member.display_name} {'left the game' if left else 'returned to the table'}",
    )
    touch(session)
    return participant
