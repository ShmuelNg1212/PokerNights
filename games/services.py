"""The only code allowed to change tables, presets, sessions and participants."""

from django.db import IntegrityError, transaction

from audit import services as audit
from groups.access import require_host
from groups.errors import RuleError
from groups.models import Member
from groups.services import clean_name
from ledger import money

from .models import GameType, SettingsPreset, StakesFields, Table


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
