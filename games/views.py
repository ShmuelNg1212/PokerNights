import datetime

from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from groups.access import member_for, require_host
import json
import uuid

from django.contrib import messages

from groups.errors import RuleError
from django.conf import settings

from groups.forms import NamesForm
from groups.http import attempt, request_id_from, attempt_bound, group_settings, keep_form
from groups import services as groups
from groups.models import Member
from ledger import money

from . import clock, rsvp, services
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
    return group_settings(group_id, "tables")


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
            return group_settings(group_id, "presets")
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
    # What choosing each preset writes into the form, as the form shows it (static/js/setup.js).
    presets = list(presets)
    for p in presets:
        p.fill = json.dumps({"game_type": p.game_type, "unit": p.unit, **{name: money.plain_amount(value, p.unit) for name, value in p.stakes().items()}})
    if request.method == "POST" and form.is_valid():
        data = {**form.cleaned_data, "preset_id": request.POST.get("preset_id") or None}
        session = attempt_bound(request, form, services.create_session, actor, data)
        if session is not None:
            return redirect("night", night_id=session.night_id)
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
def session_end_time(request, session_id):
    """A host moves the end of play earlier while the set is counting up. The time is local (Asia/Manila)."""
    session, actor = session_for(request.user, session_id)
    try:
        typed = datetime.datetime.fromisoformat(request.POST.get("ended_at", ""))
    except ValueError:
        typed = None
    if typed is None or typed.tzinfo is not None:
        messages.error(request, "Enter the date and time play ended.")
        return redirect("session", session_id=session.pk)
    ended_at = clock.whole_minute(timezone.make_aware(typed))
    saved = attempt(request, services.correct_end_time, session.pk, actor, ended_at, request.POST.get("reason", ""),
                    request_id=request_id_from(request))
    if saved is not None:
        messages.success(request, f"End time set to {clock.clock_time(ended_at)}.")
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
    """The "Add players" page: a host ticks roster players, types new names one per line, and adds them all at once."""
    session, actor = session_for(request.user, session_id)
    require_host(actor)
    selected, error = set(), ""
    posted = request.method == "POST"
    # A page drawn before several names existed sends one "name".
    data = {"names": request.POST.get("names", request.POST.get("name", ""))} if posted else None
    names_form = NamesForm(data, auto_id="new_names_%s")
    field = names_form.fields["names"]
    field.label, field.required = "New names", False
    field.help_text = "One name per line. Each joins the roster without a login and takes a seat now." if settings.ROSTER_TOOLS else "One name. They join the roster without a login and take a seat now."
    field.widget.attrs.update({"rows": 2, "data-names": ""})
    if posted:
        ids = request.POST.getlist("member_id")
        names_form.is_valid()
        lines = names_form.cleaned_data.get("names", "").splitlines()
        try:
            added = services.add_players(session.pk, actor, ids, lines, request_id_from(request))
        except RuleError as refused:
            error = str(refused)
            if isinstance(refused, services.NamesRefused):
                names_form.add_error("names", "Check the names above. Nothing was added.")
            selected = {int(value) for value in ids if value.isdecimal()}
        else:
            names = ", ".join(p.member.display_name for p in added)
            count = len(added)
            messages.success(request, f"Added {count} player{'' if count == 1 else 's'}: {names}.")
            # The set page marks these rows once, on its next view.
            request.session["players_arrived"] = {str(session.pk): [p.pk for p in added]}
            return redirect("session", session_id=session.pk)
        session.refresh_from_db()
    can_add = session.state in services.HOST_ADD_STATES
    if not can_add and not posted:
        messages.error(request, "Players cannot be added at this stage of the set.")
        return redirect("session", session_id=session.pk)

    status = dict(Participant.objects.filter(session=session).values_list("member_id", "status"))
    # Set 1 of an announced session starts with the players who said they are coming ticked.
    answers = rsvp.answers_for_set_one(session)
    if not posted and answers:
        # Only as many as the set has free seats, the first to answer first.
        joined = {m for m, st in status.items() if st == Participant.Status.JOINED}
        free = session.seat_count - len(joined)
        coming = [m for m, (state, _) in answers.items() if state == "confirmed" and m not in joined]
        selected = set(coming[:max(free, 0)])
    rows, seated_names, roster = [], [], {}
    for member in Member.objects.filter(group_id=session.group_id, status=Member.Status.ACTIVE):
        at_table = status.get(member.pk) == Participant.Status.JOINED
        rows.append({
            "member": member,
            "at_table": at_table,
            "left_earlier": status.get(member.pk) in (Participant.Status.LEFT, Participant.Status.WITHDRAWN),
            "checked": member.pk in selected and not at_table,
            "rsvp": answers.get(member.pk, (None, None)),
        })
    if answers:
        # Coming first, then the waitlist in line order, then everyone else as before.
        order = {"confirmed": 0, "waitlisted": 1}
        rows.sort(key=lambda row: (order.get(row["rsvp"][0], 2), row["rsvp"][1] or 0))
    for row in rows:
        member, at_table = row["member"], row["at_table"]
        if at_table:
            seated_names.append(member.display_name.lower())
        else:
            roster[member.display_name.lower()] = member.pk
    removed = Member.objects.filter(group_id=session.group_id, status=Member.Status.REMOVED).values_list("display_name", flat=True) if settings.ROSTER_TOOLS else []
    seated = sum(1 for row in rows if row["at_table"])
    context = {
        "session": session,
        "rows": rows,
        "error": error,
        "seats_free": session.seat_count - seated,
        "selected_count": sum(1 for row in rows if row["checked"]),
        "names_form": names_form,
        "can_add": can_add,
        "eligible_count": sum(1 for row in rows if not row["at_table"]),
        "request_id": uuid.uuid4(),
        # What the page's preview checks a typed name against. The server checks again.
        "known": json.dumps({"roster": roster, "seated": seated_names, "removed": sorted({name.lower() for name in removed}), "several": settings.ROSTER_TOOLS}),
    }
    return render(request, "games/add_players.html", context)


@require_POST
def seat_draw(request, session_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.draw_seats, session.pk, actor, request_id_from(request))
    return redirect("session", session_id=session.pk)


@require_POST
def seat_choose(request, session_id):
    """The dealer's seat. The draw stage (seats.js) sends it in the background and reads the answer."""
    session, actor = session_for(request.user, session_id)
    seat, key = request.POST.get("seat"), request_id_from(request)
    if request.headers.get("X-Requested-With") != "fetch":
        attempt(request, services.choose_seat, session.pk, actor, seat, key)
        return redirect("session", session_id=session.pk)
    try:
        draw = services.choose_seat(session.pk, actor, seat, key)
    except RuleError as error:
        return JsonResponse({"error": str(error)}, status=409)
    return JsonResponse({"draw": draw.pk, "seat": draw.dealer_seat})


@require_POST
def seat_late(request, session_id):
    session, actor = session_for(request.user, session_id)
    attempt(
        request, services.seat_late_player, session.pk, actor,
        request.POST.get("participant_id"), request.POST.get("after"), request_id_from(request),
    )
    return redirect("session", session_id=session.pk)


@require_POST
def next_set(request, night_id):
    night, actor = night_for(request.user, night_id)
    new = attempt(request, services.start_next_set, night.pk, actor)
    if new is None:
        return redirect("night", night_id=night.pk)
    messages.success(request, f"Set {new.set_number} is open. Add or remove players, then start it.")
    return redirect("session", session_id=new.pk)


def _group_manage(request, actor, mode):
    group = actor.group
    context = {"group": group, "mode": mode, "unfinished": services.group_unfinished_sets(group),
               "typed": request.POST.get("confirm_name", "")}
    if mode == "delete":
        context["has_records"] = services.group_has_records(group)
    return render(request, "games/group_manage.html", context)


def group_archive(request, group_id):
    """Confirm, then archive the group."""
    actor = member_for(request.user, group_id)
    require_host(actor)
    if request.method == "POST" and attempt(
            request, groups.archive_group, actor,
            success=f"{actor.group.name} is archived. A host can restore it from Archived groups.") is not None:
        return redirect("home")
    return _group_manage(request, actor, "archive")


@require_POST
def group_restore(request, group_id):
    actor = member_for(request.user, group_id, archived=True)
    attempt(request, groups.restore_group, actor, success=f"{actor.group.name} is restored.")
    return redirect("group", group_id=group_id)


def group_delete(request, group_id):
    """Confirm by typing the group name, then delete a group that never held money."""
    actor = member_for(request.user, group_id, archived=True)
    require_host(actor)
    if request.method == "POST":
        name = actor.group.name
        if attempt(request, _deleted, actor, request.POST.get("confirm_name", ""), success=f"Deleted the group {name}.") is not None:
            return redirect("home")
    return _group_manage(request, actor, "delete")


def _deleted(actor, confirm_name) -> bool:
    services.delete_group(actor, confirm_name)
    return True


# --- RSVP ----------------------------------------------------------------------

def _rsvp_back(request, night):
    """Back to where the answer was given: the group's Sessions tab or the session page."""
    if request.POST.get("back") == "tab":
        return redirect(reverse("group", args=[night.group_id]) + f"#coming-{night.pk}")
    return redirect(reverse("night", args=[night.pk]) + "#coming")


def _small_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


@require_POST
def night_announce(request, night_id):
    night, actor = night_for(request.user, night_id)
    raw_time, raw_seats = request.POST.get("start_time", "").strip(), request.POST.get("seat_limit", "").strip()
    start_time = None
    if raw_time:
        try:
            start_time = datetime.time.fromisoformat(raw_time)
        except ValueError:
            start_time = False
    seats = _small_int(raw_seats) if raw_seats else None
    if start_time is False:
        messages.error(request, "Enter the start time as hours and minutes, or leave it empty.")
    elif raw_seats and seats is None:
        messages.error(request, "Enter the number of seats.")
    elif attempt(request, services.announce_night, night.pk, actor, start_time=start_time, seat_limit=seats,
                 success="Announced. Players can answer now.") is not None:
        request.session.pop("announce_draft", None)
        return redirect(reverse("night", args=[night.pk]) + "#coming")
    request.session["announce_draft"] = {"night": night.pk, "start_time": raw_time, "seat_limit": raw_seats}
    return redirect(reverse("night", args=[night.pk]) + "#announce")


@require_POST
def night_rsvp(request, night_id):
    """In or Out. Without ``member`` the requester answers for themselves; with it, a host answers for that player."""
    night, actor = night_for(request.user, night_id)
    member_id = _small_int(request.POST.get("member")) if request.POST.get("member") else actor.pk
    if member_id is None:
        raise Http404("Not found")
    going = request.POST.get("going") == "in"
    attempt(request, services.answer_rsvp, night.pk, actor, member_id, going, request_id_from(request))
    return _rsvp_back(request, night)


@require_POST
def night_seats(request, night_id):
    night, actor = night_for(request.user, night_id)
    seats = _small_int(request.POST.get("seat_limit"))
    if seats is None:
        messages.error(request, "Enter the number of seats.")
    elif attempt(request, services.set_seat_limit, night.pk, actor, seats, success=f"{seats} seats.") is None:
        request.session["seats_draft"] = {"night": night.pk, "seat_limit": request.POST.get("seat_limit", "")}
    return redirect(reverse("night", args=[night.pk]) + "#coming")


@require_POST
def night_seat_now(request, night_id):
    night, actor = night_for(request.user, night_id)
    member_id = _small_int(request.POST.get("member"))
    if member_id is None:
        raise Http404("Not found")
    row = attempt(request, services.seat_from_waitlist, night.pk, actor, member_id)
    if row is not None:
        messages.success(request, f"{row.member.display_name} has a seat. The session now has {row.night.seat_limit} seats.")
    return redirect(reverse("night", args=[night.pk]) + "#coming")
