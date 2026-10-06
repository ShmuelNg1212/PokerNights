"""Pages that compose several apps. They only read; each write is a POST view in its own app."""

from datetime import datetime

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from groups.access import member_for
from groups.forms import GroupForm, NameForm
from groups.http import take_form
from games.forms import TableForm
from django.utils import timezone

from accounts import services as accounts
from audit.models import AuditEvent

from games import clock
from games import services as games
from games.access import night_for, read_only, session_for
from games.models import GameNight, GameSession, Participant, SettingsPreset, Table
from groups.models import Invite, Member
from ledger import money
from ledger import queries as ledger_queries
from ledger import services as ledger
from ledger.models import BalanceAdjustment, BuyIn, CashOut
from settlement import queries as settlement_queries

from .home import archived_groups, home_cards


def home(request):
    return render(request, "web/home.html", {"cards": home_cards(request.user), "archived_groups": archived_groups(request.user), "form": take_form(request, "home:create", GroupForm, auto_id="group_%s")})


def visible_nights(me, archived=False):
    """The group's sessions with the sets that this member can see (drafts are for hosts only)."""
    nights = GameNight.objects.filter(group=me.group).select_related("table").prefetch_related("sets")
    nights = nights.filter(archived_at__isnull=not archived)
    for night in nights:
        sets = sorted(night.sets.all(), key=lambda s: s.set_number)
        night.shown_sets = [s for s in sets if me.is_host or s.state != GameSession.State.SETUP]
        night.latest_set = night.shown_sets[-1] if night.shown_sets else None
    return nights


GROUP_VIEWS = ("sessions", "stats", "settings")


def group(request, group_id):
    """One group route with a view per tab; an unknown ``view`` shows the sessions."""
    me = member_for(request.user, group_id)
    view = request.GET.get("view")
    context = {
        "me": me,
        "group": me.group,
        "view": view if view in GROUP_VIEWS else "sessions",
        "tables": Table.objects.filter(group=me.group, archived_at__isnull=True).select_related("default_preset"),
    }
    periods = settlement_queries.stat_periods(me.group)
    # The Stats tab appears once a closed session gives it something to show.
    context["has_stats"] = bool(periods)
    if context["view"] == "settings":
        context.update(group_settings_context(request, me))
    elif context["view"] == "stats":
        context.update(group_stats_context(request, me, periods))
    else:
        nights = [n for n in visible_nights(me) if n.shown_sets]
        context["open_nights"] = [n for n in nights if not n.is_closed]
        context["closed_nights"] = [n for n in nights if n.is_closed]
        states = settlement_queries.settle_states([n.pk for n in context["closed_nights"]])
        for night in context["closed_nights"]:
            night.settle = states[night.pk]
        context["not_settled"] = sum(1 for state in states.values() if state.status != "settled")
        context["archived_nights"] = list(visible_nights(me, archived=True)) if me.is_host else []
    return render(request, "web/group.html", context)


def group_stats_context(request, me, periods) -> dict:
    """Profit or loss, sessions played and win rate for one unit and one period. Read-only."""
    unit = request.GET.get("unit")
    if unit not in periods:
        unit = money.PHP if money.PHP in periods or not periods else next(iter(periods))
    months = periods.get(unit, [])
    month = next((m for m in months if m.strftime("%Y-%m") == request.GET.get("month")), None)
    stats = settlement_queries.group_stats(me.group, unit, month) if months else []
    return {
        "stats": stats,
        "stat_members": [line.member for line in stats],
        "stat_unit": unit,
        "stat_units": [u for u in (money.PHP, money.CHIPS) if u in periods],
        "stat_month": month,
        "stat_months": months,
    }


def group_settings_context(request, me) -> dict:
    """Roster, invites, tables, presets and the rake account. Kept forms are taken only here, so they are not lost on another tab."""
    group_id = me.group_id
    members = list(Member.objects.filter(group=me.group, status=Member.Status.ACTIVE))
    rake_totals, rake_sets = ledger_queries.group_rake(me.group)
    context = {
        "members": members,
        "rake_totals": rake_totals,
        "rake_sets": rake_sets,
        "presets": SettingsPreset.objects.filter(group=me.group, archived_at__isnull=True),
    }
    if me.is_host:
        context["add_form"] = take_form(request, f"{group_id}:add", NameForm, auto_id="add_%s")
        context["table_form"] = take_form(request, f"{group_id}:table", TableForm, presets=context["presets"], auto_id="table_%s")
        for member in members:
            member.rename_form = take_form(request, f"{group_id}:rename:{member.pk}", NameForm,
                initial={"name": member.display_name}, auto_id=f"rename_{member.pk}_%s")
        context["invites"] = Invite.objects.filter(
            group=me.group, revoked_at__isnull=True, expires_at__gt=timezone.now()
        )
        context["new_invite_url"] = request.session.pop("new_invite_url", None)
        live = accounts.live_reset_links([m.user_id for m in members if m.user_id])
        for member in members:
            member.reset_link = live.get(member.user_id)
        new_link = request.session.pop("new_reset_link", None)
        if new_link:
            new_link["expires_at"] = datetime.fromisoformat(new_link["expires_at"])
        context["new_reset_link"] = new_link
    return context


def session_context(session, me) -> dict:
    """Everything the session screen shows. Used by the page and by the polling endpoint."""
    summary = ledger_queries.summary(session)
    participants = [line.participant for line in summary.lines]
    seated = sum(1 for p in participants if p.status == Participant.Status.JOINED)
    current = games.current_settings(session)
    context = {
        "session": session,
        "me": me,
        "settings": current,
        "default_buy_in": money.plain_amount(current.default_buy_in, session.unit),
        "unit": session.unit,
        "summary": summary,
        "participants": participants,
        "count_complete": len(summary.ready_lines) + len(summary.cashed_out_lines),
        "count_total": ledger_queries.count_total(summary) if session.state == GameSession.State.RECONCILIATION else None,
        "my_participant": next((p for p in participants if p.member_id == me.pk), None),
        "my_line": next((line for line in summary.lines if line.participant.member_id == me.pk), None),
        "can_buy_in": me.is_host and session.state in ledger.BUY_IN_STATES,
        "can_reverse": me.is_host and session.state in ledger.REVERSAL_STATES,
        "can_cash_out": me.is_host and session.state in ledger.CASH_OUT_STATES,
        "balance": ledger_queries.balance(summary) if session.state == GameSession.State.RECONCILIATION else None,
        "seats_free": session.seat_count - seated,
        "can_configure_rake": me.is_host and session.state in ("setup", "open") and not games.has_money(session),
        "can_join": session.state in games.JOINABLE_STATES,
        "can_manage_players": me.is_host and session.state in games.HOST_ADD_STATES,
        # A player types their own final count while the set is counting up; the host confirms it.
        "can_enter_count": settings.PLAYER_ENTRIES and not me.is_host and session.state == GameSession.State.RECONCILIATION,
    }
    played, running_ids = clock.player_clocks(session)
    for line in summary.lines:
        line.play_seconds = played.get(line.participant.pk)
        line.clock_running = line.participant.pk in running_ids
        # The row offers "Cash out" only where the ledger would accept it mid-set.
        # A host records for anyone at the table; a player records their own rebuy.
        line.can_buy_in = (
            context["can_buy_in"] and line.participant.status == Participant.Status.JOINED
            or not me.is_host and line.participant.member_id == me.pk and ledger.can_rebuy_own(session, line)
        )
        line.can_cash_out_now = (
            context["can_cash_out"] and session.state == GameSession.State.RUNNING
            and line.has_money and not line.is_cashed_out
        )
    context["set_seconds"], context["set_running"] = clock.timers([session.pk]).get(session.pk, (None, False))
    if session.state == GameSession.State.FINALIZED:
        outcome = settlement_queries.outcome(session)
        for result in outcome.results:
            result.line = summary.line_for(result.participant_id)
        context["outcome"] = outcome
        context["my_result"] = outcome.result_for(me.pk)
        context["night"] = session.night
    if context["can_manage_players"]:
        present = {p.member_id for p in participants if p.status == Participant.Status.JOINED}
        context["addable_members"] = [
            m for m in Member.objects.filter(group_id=session.group_id, status=Member.Status.ACTIVE)
            if m.pk not in present
        ]
    return context


def shown_as(me, night):
    """The member as the pages should treat them: nobody acts as a host on an archived session."""
    return read_only(me) if night.is_archived else me


def session(request, session_id):
    session, me = session_for(request.user, session_id)
    context = session_context(session, shown_as(me, session.night))
    context["real_host"] = me.is_host
    # Counts that were typed but refused are shown again, once.
    drafts = request.session.get("count_drafts", {})
    typed = drafts.pop(str(session.pk), None)
    if typed is not None:
        request.session["count_drafts"] = drafts
        for line in context["summary"].lines:
            line.count_draft = typed.get(str(line.participant.pk), "")
    return render(request, "web/session.html", context)


def session_state(request, session_id):
    """Polling endpoint: 204 while nothing changed, else a full snapshot of the live region."""
    session, me = session_for(request.user, session_id)
    if request.GET.get("v") == str(session.version):
        return HttpResponse(status=204)
    html = render_to_string("web/_session_live.html", session_context(session, shown_as(me, session.night)), request=request)
    return JsonResponse({"version": session.version, "state": session.state, "html": html})


def session_log(request, session_id):
    """Everything recorded for one session, including reversed and voided rows."""
    session, me = session_for(request.user, session_id)
    context = {
        "session": session,
        "me": me,
        "participants": Participant.objects.filter(session=session).select_related("member"),
        "settings_versions": session.settings_versions.select_related("created_by").order_by("number"),
        "buy_ins": BuyIn.objects.filter(session=session).select_related(
            "participant__member", "recorded_by", "reversal__recorded_by", "rake_entry"
        ),
        "cash_outs": CashOut.objects.filter(session=session).select_related(
            "participant__member", "recorded_by", "reversal__recorded_by"
        ),
        "adjustments": BalanceAdjustment.objects.filter(session=session).select_related(
            "participant__member", "recorded_by"
        ),
        "outcome": settlement_queries.outcome(session),
        "events": AuditEvent.objects.filter(session_id=session.pk).select_related("actor"),
        "play_periods": session.play_periods.all(),
        "set_seconds": clock.set_seconds(session),
        "played": clock.player_seconds(session),
    }
    return render(request, "web/session_log.html", context)


def night(request, night_id):
    """The session page: its sets, in order."""
    night, host = night_for(request.user, night_id)
    me = shown_as(host, night)
    # The session's sets are read once, and each figure over them in one query whatever their number.
    by_number = list(night.sets.order_by("set_number"))
    sets = [s for s in by_number if host.is_host or s.state != GameSession.State.SETUP]
    timers = clock.timers([s.pk for s in sets])
    for one in sets:
        one.play_seconds, one.clock_running = timers.get(one.pk, (None, False))
    timed = [one.play_seconds for one in sets if one.play_seconds is not None]
    context = {"night": night, "me": me, "sets": sets, "latest_set": sets[-1] if sets else None, "unit": night.unit}
    context["total_play_seconds"] = sum(timed) if timed else None
    context["total_rake"] = ledger_queries.rake_total([s.pk for s in sets])
    context["can_start_next_set"] = (
        me.is_host and not night.is_closed and not any(s.state in games.IN_PLAY_STATES for s in sets)
    )
    State = GameSession.State
    all_sets = sorted(by_number, key=lambda s: (s.game_date, s.pk), reverse=True)  # the model's own order
    unfinished = [s for s in all_sets if s.state not in (State.FINALIZED, State.CANCELED)]
    outcome = settlement_queries.night_outcome(night)
    context.update({
        "outcome": outcome,
        "my_standing": outcome.standing_for(me.pk),
        "my_transfers": outcome.transfers_for(me.pk),
        "finalized_count": sum(1 for s in all_sets if s.state == State.FINALIZED),
        "unfinished_sets": unfinished,
        "can_close": me.is_host and not night.is_closed and not unfinished
        and any(s.state == State.FINALIZED for s in all_sets),
    })
    if night.is_closed and not night.is_archived:
        context["recap"] = settlement_queries.night_recap(
            night, outcome.standings, {pk: seconds for pk, (seconds, _) in timers.items()}
        )
    if host.is_host:
        context["manage"] = {
            "unfinished": [s for s in all_sets if s.state in games.UNFINISHED_STATES],
            "has_records": games.night_has_records(night),
        }
    return render(request, "web/night.html", context)
