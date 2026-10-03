"""The only code allowed to change tables, presets, sessions and participants."""

import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone

from audit import services as audit
from groups.access import require_host
from groups.errors import RuleError
from groups.models import Member
from groups.services import clean_name
from ledger import money

from .models import GameSession, GameType, Participant, SettingsPreset, SettingsVersion, StakesFields, Table


def validated_stakes(data: dict) -> dict:
    """The six stakes values from ``data``, checked. Raises RuleError with a clear message."""
    stakes = {}
    for name in StakesFields.STAKES_FIELDS:
        value = data.get(name)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise RuleError("Each blind, buy-in amount and chip count must be more than zero.")
        stakes[name] = value
    if stakes["small_blind_centavos"] > stakes["big_blind_centavos"]:
        raise RuleError("The small blind cannot be more than the big blind.")
    if not stakes["min_buy_in_centavos"] <= stakes["default_buy_in_centavos"] <= stakes["max_buy_in_centavos"]:
        raise RuleError("The usual buy-in must be between the minimum and the maximum buy-in.")
    return stakes


def chip_rate(stakes) -> tuple[int, int]:
    """The reduced chip rate that a preset or settings version defines."""
    if not isinstance(stakes, dict):
        stakes = stakes.stakes()
    return money.reduce_rate(stakes["default_buy_in_centavos"], stakes["chips_per_buy_in"])


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
    """Add a settings version. With money in the session, the value of a chip cannot change."""
    require_host(actor)
    session = lock_session(session_id, actor.group_id)
    if session.state not in (State.SETUP, State.OPEN, State.RUNNING):
        raise RuleError("Settings cannot change after play has ended.")
    stakes = validated_stakes(data)
    if session.rate is not None and chip_rate(stakes) != session.rate:
        raise RuleError(
            "Buy-ins are already recorded, so the value of a chip cannot change. "
            "Keep the same pesos-to-chips ratio, or reverse the buy-ins first."
        )
    previous = current_settings(session)
    if previous.stakes() == stakes:
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
    "end": "Ended play; counting chips",
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
        if session.rate is not None:
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
