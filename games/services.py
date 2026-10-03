"""The only code allowed to change tables, presets, sessions and participants."""

import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone

from audit import services as audit
from groups.access import require_host
from groups.errors import RuleError
from groups.models import Member
from groups.services import clean_name

from .models import GameSession, GameType, Participant, SettingsPreset, SettingsVersion, StakesFields, Table, Unit


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


def lock_session(session_id, group_id) -> GameSession:
    """The session row, locked for the rest of the transaction. Every session write starts here."""
    session = (
        GameSession.objects.select_for_update().select_related("table").filter(pk=session_id, group_id=group_id).first()
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
    """Create a game in setup, with settings version 1."""
    require_host(actor)
    table = Table.objects.filter(group=actor.group, pk=data.get("table_id"), archived_at__isnull=True).first()
    if table is None:
        raise RuleError("Select a table of this group.")
    preset = None
    if data.get("preset_id"):
        preset = SettingsPreset.objects.filter(group=actor.group, pk=data["preset_id"]).first()
    session = GameSession.objects.create(
        group=actor.group,
        table=table,
        game_date=_clean_date(data.get("game_date")),
        location=(data.get("location") or "").strip()[:120],
        game_type=_game_type(data.get("game_type")),
        unit=_unit(data.get("unit")),
        seat_count=table.seat_count,
        created_by=actor.user,
    )
    SettingsVersion.objects.create(
        session=session, number=1, preset=preset, created_by=actor.user, **validated_stakes(data)
    )
    audit.record(
        "session.created", actor=actor.user, group_id=actor.group_id, session_id=session.pk, target=session,
        summary=f"Created a game at {table.name} for {session.game_date:%Y-%m-%d}",
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
        session.unit = unit
        session.save(update_fields=["unit"])
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
def transition(session_id, actor: Member, action: str, reason: str = "") -> GameSession:
    """Move the session through its lifecycle. Finalization is a separate service."""
    require_host(actor)
    if action not in TRANSITIONS:
        raise RuleError("Unknown action.")
    session = lock_session(session_id, actor.group_id)
    allowed_from, target = TRANSITIONS[action]
    if session.state not in allowed_from:
        raise RuleError(f"This game is {session.get_state_display().lower()}, so that action is not available.")
    reason = (reason or "").strip()
    if action == "close" and session.participants.filter(status=Participant.Status.JOINED).exists():
        raise RuleError("Players have joined. Remove them first, or cancel the game.")
    if action == "cancel":
        if has_money(session):
            raise RuleError("Buy-ins are recorded. Reverse them first, or finish and finalize the game.")
        if session.state != State.SETUP and not reason:
            raise RuleError("Give a reason for canceling.")
        session.cancel_reason = reason[:255]
    if action == "start" and session.started_at is None:
        session.started_at = timezone.now()
    session.state = target
    session.save(update_fields=["state", "started_at", "cancel_reason"])
    audit.record(
        f"session.{action}", actor=actor.user, group_id=actor.group_id, session_id=session.pk, target=session,
        summary=ACTION_LABELS[action], reason=reason,
    )
    touch(session)
    return session


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
    audit.record(
        "participant.joined", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=participant,
        summary=f"{member.display_name} joined" if is_self else f"Added {member.display_name}",
    )
    touch(session)
    return participant


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
    participant.status = wanted
    participant.left_at = timezone.now() if left else None
    participant.save(update_fields=["status", "left_at"])
    audit.record(
        "participant.left" if left else "participant.returned", actor=actor.user, group_id=session.group_id,
        session_id=session.pk, target=participant,
        summary=f"{participant.member.display_name} {'left the game' if left else 'returned to the table'}",
    )
    touch(session)
    return participant
