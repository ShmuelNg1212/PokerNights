from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from groups.access import member_for, require_host
import uuid

from django.contrib import messages

from groups.errors import RuleError
from groups.forms import NameForm
from groups.http import attempt, request_id_from, attempt_bound, keep_form
from groups.models import Member

from . import services
from .access import night_for, session_for
from .forms import PresetForm, SessionForm, SettingsForm, TableForm
from .models import Participant, SettingsPreset, Table


@require_POST
def create_table(request, group_id):
    actor = member_for(request.user, group_id)
    require_host(actor)
    form = TableForm(request.POST, presets=SettingsPreset.objects.filter(group=actor.group, archived_at__isnull=True))
    if not form.is_valid() or attempt_bound(request, form, services.create_table, actor,
            form.cleaned_data["name"], form.cleaned_data["seat_count"],
            form.cleaned_data["default_preset"] or None, success="Table added.") is None:
        keep_form(request, f"{group_id}:table", form)
    return redirect("group", group_id=group_id)


def preset_form(request, group_id, preset_id=None):
    actor = member_for(request.user, group_id)
    require_host(actor)
    preset = None
    initial = {"game_type": "nlh"}
    if preset_id is not None:
        preset = get_object_or_404(SettingsPreset, group=actor.group, pk=preset_id, archived_at__isnull=True)
        initial = {"name": preset.name, "game_type": preset.game_type, "unit": preset.unit, **preset.stakes()}
    form = PresetForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        saved = attempt_bound(request, form, services.save_preset, actor, form.cleaned_data, preset_id=preset_id, success="Preset saved.")
        if saved is not None:
            return redirect("group", group_id=group_id)
    return render(request, "games/preset_form.html", {"form": form, "group": actor.group, "preset": preset})


def session_new(request, group_id):
    actor = member_for(request.user, group_id)
    require_host(actor)
    tables = Table.objects.filter(group=actor.group, archived_at__isnull=True).select_related("default_preset")
    presets = SettingsPreset.objects.filter(group=actor.group, archived_at__isnull=True)
    preset = presets.filter(pk=request.GET.get("preset") or 0).first()
    if preset is None and not request.GET.get("preset"):
        preset = next((table.default_preset for table in tables if table.default_preset), None) or presets.first()
    initial = {"game_type": preset.game_type, "unit": preset.unit, **preset.stakes()} if preset else {}
    form = SessionForm(request.POST or None, initial=initial, tables=tables)
    if request.method == "POST" and form.is_valid():
        data = {**form.cleaned_data, "preset_id": request.POST.get("preset_id") or None}
        session = attempt_bound(request, form, services.create_session, actor, data)
        if session is not None:
            return redirect("session", session_id=session.pk)
    context = {"form": form, "group": actor.group, "tables": tables, "presets": presets, "preset": preset}
    return render(request, "games/session_form.html", context)


def session_settings(request, session_id):
    session, actor = session_for(request.user, session_id)
    require_host(actor)
    form = SettingsForm(
        request.POST or None, initial={**services.current_settings(session).stakes(), **services.current_settings(session).rake()}, unit=session.unit,
        unit_locked=services.has_money(session),
    )
    if request.method == "POST" and form.is_valid():
        saved = attempt_bound(request, form, services.update_settings, session.pk, actor, form.cleaned_data, request_id=request_id_from(request), success="Settings saved.")
        if saved is not None:
            return redirect("session", session_id=session.pk)
    return render(request, "games/settings_form.html", {"form": form, "session": session, "request_id": request.POST.get("request_id") or uuid.uuid4()})


@require_POST
def session_transition(request, session_id):
    session, actor = session_for(request.user, session_id)
    action = request.POST.get("action", "")
    options = {"request_id": request_id_from(request), "opening_buy_ins": request.POST.get("opening_buy_ins") == "on"} if action == "start" else {}
    attempt(request, services.transition, session.pk, actor, action, request.POST.get("reason", ""), **options)
    return redirect("session", session_id=session.pk)


@require_POST
def participant_add(request, session_id):
    """A player joins (no member_id), or a host adds a roster player."""
    session, actor = session_for(request.user, session_id)
    attempt(request, services.add_participant, session.pk, actor, request.POST.get("member_id") or actor.pk)
    return redirect("session", session_id=session.pk)


@require_POST
def participant_withdraw(request, session_id, participant_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.withdraw_participant, session.pk, actor, participant_id)
    return redirect("session", session_id=session.pk)


@require_POST
def participant_left(request, session_id, participant_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.set_left, session.pk, actor, participant_id, request.POST.get("left", "1") == "1")
    return redirect("session", session_id=session.pk)


def participants_add(request, session_id):
    """The "Add players" picker: a host ticks several members and confirms once."""
    session, actor = session_for(request.user, session_id)
    require_host(actor)
    selected, error = set(), ""
    creating = request.method == "POST" and request.POST.get("action") == "new"
    new_form = NameForm(request.POST if creating else None, auto_id="new_player_%s")
    new_form.fields["name"].label = "Player name"
    if request.method == "POST":
        ids = request.POST.getlist("member_id")
        try:
            if creating:
                if not new_form.is_valid():
                    raise RuleError("Check the player name. Nothing was added.")
                added = services.add_new_player(session.pk, actor, new_form.cleaned_data["name"], request_id_from(request))
            else:
                added = services.add_participants(session.pk, actor, ids, request_id_from(request))
        except RuleError as refused:
            error = str(refused)
            if creating and not new_form.errors:
                new_form.add_error("name", error)
            selected = {int(value) for value in ids if value.isdecimal()}
        else:
            names = ", ".join(p.member.display_name for p in added)
            count = len(added)
            messages.success(request, f"Added {count} player{'' if count == 1 else 's'}: {names}.")
            return redirect("session", session_id=session.pk)
        session.refresh_from_db()
    can_add = session.state in services.HOST_ADD_STATES
    if not can_add and not creating:
        messages.error(request, "Players cannot be added at this stage of the game.")
        return redirect("session", session_id=session.pk)

    status = dict(Participant.objects.filter(session=session).values_list("member_id", "status"))
    rows = []
    for member in Member.objects.filter(group_id=session.group_id, status=Member.Status.ACTIVE):
        at_table = status.get(member.pk) == Participant.Status.JOINED
        rows.append({
            "member": member,
            "at_table": at_table,
            "left_earlier": status.get(member.pk) in (Participant.Status.LEFT, Participant.Status.WITHDRAWN),
            "checked": member.pk in selected and not at_table,
        })
    seated = sum(1 for row in rows if row["at_table"])
    context = {
        "session": session,
        "rows": rows,
        "error": error,
        "seats_free": session.seat_count - seated,
        "selected_count": sum(1 for row in rows if row["checked"]),
        "new_form": new_form,
        "new_request_id": uuid.uuid4(),
        "can_add": can_add,
        "eligible_count": sum(1 for row in rows if not row["at_table"]),
        "request_id": uuid.uuid4(),
    }
    return render(request, "games/add_players.html", context)


@require_POST
def next_set(request, night_id):
    night, actor = night_for(request.user, night_id)
    new = attempt(request, services.start_next_set, night.pk, actor)
    if new is None:
        return redirect("night", night_id=night.pk)
    messages.success(request, f"Set {new.set_number} is open. Add or remove players, then start it.")
    return redirect("session", session_id=new.pk)
