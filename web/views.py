"""Pages that compose several apps. They only read; each write is a POST view in its own app."""

from datetime import datetime
import uuid

from django.conf import settings
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse

from groups.access import member_for
from groups.forms import GroupForm, MemberForm, NameForm, NamesForm
from groups.http import take_form
from games.forms import TableForm
from django.utils import timezone

from accounts import services as accounts
from audit.models import AuditEvent

from games import chips, clock
from games import rsvp
from games import seats as seat_draws
from games import services as games
from games.access import night_for, read_only, session_for
from games.models import GameNight, GameSession, Participant, SettingsPreset, Table
from groups import services as groups
from groups.models import GroupRakeAccount, Invite, Member
from ledger import money
from ledger import chip_views
from ledger import queries as ledger_queries
from ledger import services as ledger
from ledger.models import BalanceAdjustment, BuyIn, CashOut
from notify import services as notify
from settlement import queries as settlement_queries

from . import profile as profile_page
from . import stats as stats_pages
from . import prep
from . import sessions_tab
from . import share
from .home import archived_groups, home_cards


def home(request):
    return render(request, "web/home.html", {
        "cards": home_cards(request.user), "archived_groups": archived_groups(request.user),
        "form": take_form(request, "home:create", GroupForm, auto_id="group_%s"),
    })


def profile(request):
    """The person's own record across their groups, and their name and password."""
    return render(request, "web/profile.html", profile_page.profile_context(request, request.user))


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
        context.update(stats_pages.board_context(request, me, periods))
    else:
        context.update(sessions_tab.sessions_context(me, request.GET.get("past")))
    return render(request, "web/group.html", context)


def player(request, group_id, member_id):
    """One player's record in the group. Open to every member; the player may have left the group."""
    me = member_for(request.user, group_id)
    member = Member.objects.filter(group_id=group_id, pk=member_id).first()
    if member is None:
        raise Http404("Not found")
    periods = settlement_queries.stat_periods(me.group)
    context = {"me": me, "group": me.group, **stats_pages.player_context(request, me, member, periods)}
    return render(request, "web/player.html", context)


def activity_label(found, today) -> str:
    """"12 sessions · last played Oct 1" from ``settlement.queries.roster_activity``; the year when it is not this one."""
    if not found:
        return "No sessions yet"
    sessions, last = found
    when = f"{last:%b} {last.day}" + (f", {last.year}" if last.year != today.year else "")
    return f"{sessions} session{'' if sessions == 1 else 's'} · last played {when}"


PAST_INVITES = 10


def invite_rows(request, me) -> dict:
    """Active invites with their links where they can be made again, the new one marked; the last few that stopped working."""
    now = timezone.now()
    made = list(Invite.objects.filter(group=me.group).select_related("created_by").order_by("-created_at", "-id"))
    # The name the group knows the host by; an account that has left keeps its username.
    names = dict(Member.objects.filter(group=me.group, user_id__in={i.created_by_id for i in made}).values_list("user_id", "display_name"))
    for invite in made:
        invite.by = names.get(invite.created_by_id) or invite.created_by.username
    new = request.session.pop("new_invite", None)
    active, past = [], []
    for invite in made:
        if invite.ending(now) is None:
            token = groups.invite_link_token(invite) if settings.INVITE_LINKS_SHOWN else None
            invite.url = request.build_absolute_uri(reverse("invite_accept", args=[token])) if token else None
            invite.arrived = invite.pk == new
            invite.field_id = f"invite-link-{invite.pk}"
            active.append(invite)
        elif len(past) < PAST_INVITES:
            invite.ended = invite.ending(now)
            past.append(invite)
    return {
        "invites": active,
        "past_invites": past,
        "invite_left": request.session.pop("invite_left", False),
        "new_invite_url": request.session.pop("new_invite_url", None),
        "invite_links_shown": settings.INVITE_LINKS_SHOWN,
    }


def group_settings_context(request, me) -> dict:
    """Roster, invites, tables, presets and the rake account. Kept forms are taken only here, so they are not lost on another tab."""
    group_id = me.group_id
    tools = settings.ROSTER_TOOLS
    members = list(Member.objects.filter(group=me.group, status=Member.Status.ACTIVE))
    removed = list(Member.objects.filter(group=me.group, status=Member.Status.REMOVED)) if tools and me.is_host else []
    # By name whatever its capitals; the database puts "Zed" before "ana".
    for people in (members, removed):
        people.sort(key=lambda member: (member.display_name.lower(), member.pk))
    if tools:
        activity = settlement_queries.roster_activity([m.pk for m in members + removed])
        today = timezone.localdate()
        arrived = set(request.session.pop("roster_arrived", []))
        for member in members + removed:
            member.activity_label = activity_label(activity.get(member.pk), today)
            member.arrived = member.pk in arrived
            if member.pk == me.pk:
                member.own_form = take_form(request, f"{group_id}:me", NameForm,
                    initial={"name": member.display_name}, auto_id="me_%s")
    rake_totals, rake_sets = ledger_queries.group_rake(me.group)
    context = {
        "members": members,
        "removed_members": removed,
        "roster_tools": tools,
        "roster_left": request.session.pop("roster_left", False),
        "rake_totals": rake_totals,
        "rake_sets": rake_sets,
        "rake_settlement": GroupRakeAccount.objects.filter(group=me.group).values_list("settlement", flat=True).first()
        or GroupRakeAccount.Settlement.RETURNED,
        "rake_settlement_choices": GroupRakeAccount.Settlement.choices,
        "presets": SettingsPreset.objects.filter(group=me.group, archived_at__isnull=True),
        "chip_presets": [{"preset": preset, "rows": chips.named(preset.values)} for preset in games.chip_presets_for(me.group)],
    }
    if me.is_host:
        context["group_form"] = take_form(request, f"{group_id}:group", GroupForm,
            initial={"name": me.group.name}, auto_id="group_name_%s")
        context["add_form"] = take_form(request, f"{group_id}:add", NamesForm if tools else NameForm, auto_id="add_%s")
        context["table_form"] = take_form(request, f"{group_id}:table", TableForm, presets=context["presets"], auto_id="table_%s")
        for member in members:
            member.rename_form = take_form(request, f"{group_id}:rename:{member.pk}", MemberForm if tools else NameForm,
                initial={"name": member.display_name, "contact": member.contact}, auto_id=f"rename_{member.pk}_%s")
        context.update(invite_rows(request, me))
        live = accounts.live_reset_links([m.user_id for m in members if m.user_id])
        for member in members:
            member.reset_link = live.get(member.user_id)
        claims = groups.live_claim_links([m.pk for m in members if not m.user_id])
        for member in members:
            member.claim_link = claims.get(member.pk)
        new_claim = request.session.pop("new_claim_link", None)
        if new_claim:
            new_claim["expires_at"] = datetime.fromisoformat(new_claim["expires_at"])
        context["new_claim_link"] = new_claim
        context["claim_links"] = settings.CLAIM_LINKS
        new_link = request.session.pop("new_reset_link", None)
        if new_link:
            new_link["expires_at"] = datetime.fromisoformat(new_link["expires_at"])
        context["new_reset_link"] = new_link
    return context


ENDED_STATES = (GameSession.State.RECONCILIATION, GameSession.State.FINALIZED, GameSession.State.CANCELED)
UNSET = object()


def later_set(session):
    """The session's latest set after this one that a player can join or play: where an ended set's page points.

    Asked only for an ended set, so a set in play costs no query. A draft is never shown to players.
    """
    if not settings.NEXT_SET_NOTICE or session.state not in ENDED_STATES:
        return None
    return (
        GameSession.objects.filter(night_id=session.night_id, set_number__gt=session.set_number,
                                   state__in=(GameSession.State.OPEN, GameSession.State.RUNNING))
        .order_by("-set_number").first()
    )


def next_step(night, me, sets=None, member_ids=None) -> dict:
    """What a host can do once no set is in play: play the next set, or settle up. Empty for anyone else.

    The final set page and the session page show the same choice from this one answer.
    """
    if not me.is_host or night.is_closed or night.is_archived:
        return {}
    sets = list(night.sets.order_by("set_number")) if sets is None else sets
    State = GameSession.State
    unfinished = [s for s in sets if s.state not in (State.FINALIZED, State.CANCELED)]
    finalized = sum(1 for s in sets if s.state == State.FINALIZED)
    step = {
        "can_start_next_set": not any(s.state in games.IN_PLAY_STATES for s in sets),
        "next_set_number": sets[-1].set_number + 1 if sets else 1,
        "unfinished_sets": unfinished,
        "finalized_count": finalized,
        "can_close": not unfinished and finalized > 0,
        "reopen_on": settings.REOPENING,
    }
    if step["can_close"] and settings.CARRY_DEBTS:
        # Earlier unpaid transfers between two of tonight's players, which closing can fold into this list.
        step["carryable"] = settlement_queries.carryable(night, member_ids)
    return step


def live_version(session, later):
    """What the set page's poll compares: the set's version, a number as before. An ended set's page
    also changes when a later set starts, without a write to the ended set (Start next set does not
    lock it), so then it is "{version}.{later set}". A final set's page shows the session's next step,
    which changes when another set moves or the session closes, so it also carries their states."""
    version = f"{session.version}.{later.pk}" if later else session.version
    if session.state != GameSession.State.FINALIZED:
        return version
    states = GameSession.objects.filter(night_id=session.night_id).order_by("pk").values_list("pk", "state")
    status = GameNight.objects.filter(pk=session.night_id).values_list("status", flat=True).first()
    return f"{version}:{status}:" + ",".join(f"{pk}{state[0]}" for pk, state in states)


def session_context(session, me, *, later=UNSET) -> dict:
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
        "end_time_request_id": uuid.uuid4(),
        "count_complete": len(summary.ready_lines) + len(summary.cashed_out_lines),
        "count_total": ledger_queries.count_total(summary) if session.state == GameSession.State.RECONCILIATION else None,
        "my_participant": next((p for p in participants if p.member_id == me.pk), None),
        "my_line": next((line for line in summary.lines if line.participant.member_id == me.pk), None),
        "can_buy_in": me.is_host and session.state in ledger.BUY_IN_STATES,
        "can_reverse": me.is_host and session.state in ledger.REVERSAL_STATES,
        "can_cash_out": me.is_host and session.state in ledger.CASH_OUT_STATES,
        "reopen_on": settings.REOPENING,
        "balance": ledger_queries.balance(summary) if session.state == GameSession.State.RECONCILIATION else None,
        "seats_free": session.seat_count - seated,
        "can_configure_rake": me.is_host and session.state in ("setup", "open") and not games.has_money(session),
        "can_join": session.state in games.JOINABLE_STATES,
        "can_manage_players": me.is_host and session.state in games.HOST_ADD_STATES,
        # A player types their own final count while the set is counting up; the host confirms it.
        "can_enter_count": settings.PLAYER_ENTRIES and not me.is_host and session.state == GameSession.State.RECONCILIATION,
        "any_entered": any(line.entered for line in summary.lines),
        "chip_values": chip_views.denominations(session.night),
        "prep": prep.states(session, summary, me),
    }
    later = later_set(session) if later is UNSET else later
    context["later_set"], context["live_version"] = later, live_version(session, later)
    if later is not None:
        context["at_later_table"] = later.participants.filter(member=me, status=Participant.Status.JOINED).exists()
    if settings.SEAT_DRAW and session.state in ("open", "running"):
        seating = seat_draws.seating(session, participants) if getattr(session, "has_seat_draw", True) else None
        live = not session.night.is_archived
        context["seating"] = seating
        context["can_draw_seats"] = live and me.is_host and session.state == "open" and seated >= 2
        context["can_choose_seat"] = (
            live and seating is not None and seating.state == "choosing" and session.state == "open"
            and (me.is_host or seating.dealer.member_id == me.pk)
        )
        context["can_seat_late"] = live and me.is_host and session.state == "running" and seating is not None and seating.state == "seated"
    played, running_ids = clock.player_clocks(session)
    for line in summary.lines:
        if (session.night.chip_values and session.state == GameSession.State.RECONCILIATION
                and line.has_money and not line.is_cashed_out and not session.night.is_archived
                and (me.is_host or context["can_enter_count"] and line.participant.member_id == me.pk
                     and line.count is None)):
            line.chip_form = chip_views.form_context(session, line.participant, me)
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
    # Every player is cashed out and the books differ: the rows show each player's in, out and net,
    # and mark a hand-typed cash-out that differs from the count it replaced.
    books = context["balance"]
    context["books_off"] = bool(books and books.counted and not books.ok)
    if context["books_off"]:
        # Only a record that moves the books the way they are off can explain the gap: a cash-out typed
        # higher than its count when there is too much, lower when money is missing.
        for pk, gap in ledger_queries.count_gaps(summary).items():
            moved = gap[1] - gap[0]
            if (moved > 0) == (books.difference > 0):
                line = summary.line_for(pk)
                line.count_gap, line.count_gap_full, line.count_gap_moved = gap, moved == books.difference, abs(moved)
                line.count_gap_word = "more" if moved > 0 else "less"
    context["set_seconds"], context["set_running"] = clock.timers([session.pk]).get(session.pk, (None, False))
    if session.state == GameSession.State.FINALIZED:
        outcome = settlement_queries.outcome(session)
        for result in outcome.results:
            result.line = summary.line_for(result.participant_id)
        context["outcome"] = outcome
        context["my_result"] = outcome.result_for(me.pk)
        context["night"] = session.night
        if later is None:
            context.update(next_step(session.night, me))
        context["can_reopen"] = me.is_host and settings.REOPENING and not session.night.is_archived
        # A second or later revision says what was corrected: the reason the one before it was reopened.
        if outcome.finalization.revision > 1:
            context["correction"] = (
                session.finalizations.filter(is_current=False).select_related("voided_by").order_by("-revision").first()
            )
    if ledger.is_reopened(session):
        context["reopening"] = session.finalizations.select_related("voided_by").order_by("-revision").first()
        context["can_add_missed"] = me.is_host
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
    chip_drafts = request.session.pop("chip_count_drafts", {})
    for line in context["summary"].lines:
        draft = chip_drafts.get(str(line.participant.pk))
        if draft and getattr(line, "chip_form", None):
            line.chip_form = chip_views.form_context(session, line.participant, me, draft)
    # A notice that this player was put in the set has done its job once they open it.
    notify.mark_seen(request.user, session.pk)
    # Players just added on Add players are marked once (static/js/flow.js).
    arrived = request.session.get("players_arrived", {})
    if str(session.pk) in arrived:
        context["arrived"] = set(arrived.pop(str(session.pk)))
        request.session["players_arrived"] = arrived
    # Counts that were typed but refused are shown again, once.
    drafts = request.session.get("count_drafts", {})
    typed = drafts.pop(str(session.pk), None)
    if typed is not None:
        request.session["count_drafts"] = drafts
        chip_drafts = typed.get("chips", {})
        for line in context["summary"].lines:
            line.count_draft = typed.get(str(line.participant.pk), "")
            line.chip_draft = chip_drafts.get(str(line.participant.pk), "")
    return render(request, "web/session.html", context)


def session_state(request, session_id):
    """Polling endpoint: 204 while nothing changed, else a full snapshot of the live region."""
    session, me = session_for(request.user, session_id)
    later = later_set(session)
    version = live_version(session, later)
    if request.GET.get("v") == str(version):
        return HttpResponse(status=204)
    html = render_to_string("web/_session_live.html", session_context(session, shown_as(me, session.night), later=later), request=request)
    return JsonResponse({"version": version, "state": session.state, "html": html})


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
        "replaced": session.finalizations.filter(is_current=False).select_related("finalized_by", "voided_by")
        .prefetch_related("results__participant__member").order_by("-revision"),
        "events": AuditEvent.objects.filter(session_id=session.pk).select_related("actor"),
        "play_periods": session.play_periods.all(),
        "set_seconds": clock.set_seconds(session),
        "played": clock.player_seconds(session),
    }
    return render(request, "web/session_log.html", context)


def _stamp_answer(request, stamp):
    """204 while the asker's stamp still holds, else the new one."""
    if request.GET.get("v") == stamp:
        return HttpResponse(status=204)
    response = JsonResponse({"stamp": stamp})
    response["Cache-Control"] = "no-store"
    return response


def home_state(request):
    """Polling endpoint of Your groups, over the requester's own groups (nightlive.js)."""
    group_ids = Member.objects.filter(
        user=request.user, status=Member.Status.ACTIVE, group__archived_at__isnull=True
    ).values_list("group_id", flat=True)
    return _stamp_answer(request, settlement_queries.hub_stamp(list(group_ids)))


def group_state(request, group_id):
    """Polling endpoint of a group's Sessions tab."""
    me = member_for(request.user, group_id)
    return _stamp_answer(request, settlement_queries.hub_stamp([me.group_id]))


def night_state(request, night_id):
    """Polling endpoint of the session page: 204 while nothing it shows has changed, else the new stamp.

    The page then fetches itself and is redrawn in place (nightlive.js).
    """
    night, _ = night_for(request.user, night_id)
    return _stamp_answer(request, settlement_queries.night_stamp(night))


def _rsvp_context(request, night, me, by_number) -> dict:
    """Who is coming, or, for a host before it is announced, the Announce card."""
    first = by_number[0] if by_number else None
    if night.announced_at is not None:
        board = rsvp.boards([night], me, sets={night.pk: first})[night.pk]
        notify.mark_night_seen(request.user, night.pk)
        draft = request.session.pop("seats_draft", None)
        # Before play, the page is about who is coming: the empty results and sets wait.
        return {"board": board, "seats_draft": draft["seat_limit"] if draft and draft.get("night") == night.pk else "",
                "before_play": not any(s.started_at for s in by_number)}
    if me.is_host and not night.is_archived and not night.is_closed and first is not None \
            and first.state in rsvp.ANSWER_STATES:
        draft = request.session.pop("announce_draft", None)
        draft = draft if draft and draft.get("night") == night.pk else {}
        told = games.announce_audience(night.group_id, request.user.pk).count()
        return {"announce": {"start_time": draft.get("start_time", ""),
                             "seat_limit": draft.get("seat_limit", night.table.seat_count), "told": told}}
    return {}


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
    context["chip_values"] = chip_views.denominations(night)
    context["total_play_seconds"] = sum(timed) if timed else None
    context["total_rake"] = ledger_queries.rake_total([s.pk for s in sets])
    State = GameSession.State
    all_sets = sorted(by_number, key=lambda s: (s.game_date, s.pk), reverse=True)  # the model's own order
    outcome = settlement_queries.night_outcome(night)
    context.update({
        "outcome": outcome,
        "my_standing": outcome.standing_for(me.pk),
        "my_transfers": outcome.transfers_for(me.pk),
        "my_part": outcome.part_for(me.pk),
        "finalized_count": sum(1 for s in all_sets if s.state == State.FINALIZED),
    })
    context.update(next_step(night, me, by_number, {standing.pk for standing in outcome.standings}))
    # Open set N leads to the latest set that still needs the host or the players; finished ones are under Sets.
    context["latest_set"] = next((s for s in reversed(sets) if s.state not in (State.FINALIZED, State.CANCELED)), None)
    context["my_makeup"] = outcome.makeup_for(me.pk)
    context.update(_rsvp_context(request, night, me, by_number))
    if not night.is_archived:
        # The mark nightlive.js polls with, from rows this page has already read.
        context["stamp"] = settlement_queries.stamp_from(
            night, [(s.pk, s.state, s.finalized_at) for s in by_number], outcome.plan.pk if outcome.plan else None,
            len(outcome.replaced), (len(outcome.payments), sum(1 for p in outcome.payments if p.active)),
            sum(1 for t in outcome.transfers if t.carried), rsvp=context["board"].mark if context.get("board") else None,
        )
    context["replaced_plans"] = outcome.replaced
    context["my_table_payments"] = [
        p for p in outcome.table_payments if p.active and me.pk in (p.payer_id, p.payee_id)
    ]
    if host.is_host and not night.is_closed and not night.is_archived:
        context["players"] = settlement_queries.session_players(night)
        context["values"] = {}
    if not night.is_closed and outcome.replaced:
        context["reopening"] = outcome.replaced[-1]
    if host.is_host and night.is_closed and not night.is_archived and settings.REOPENING:
        context["reopen"] = {"paid": outcome.paid_count, "carried": next((t.carried for t in outcome.transfers if t.carried), None)}
    if night.is_closed and not night.is_archived:
        context["recap"] = settlement_queries.night_recap(
            night, outcome.standings, {pk: seconds for pk, (seconds, _) in timers.items()},
            results=outcome.results, viewer_id=me.pk,
        )
        if settings.SHARE_RESULTS and outcome.plan is not None:
            context["share"] = share.card(night, outcome, context["recap"])
    if host.is_host:
        context["manage"] = {
            "unfinished": [s for s in all_sets if s.state in games.UNFINISHED_STATES],
            "has_records": games.night_has_records(night),
        }
    return render(request, "web/night.html", context)
