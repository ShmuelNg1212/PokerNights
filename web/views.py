"""Pages that compose several apps. They only read; each write is a POST view in its own app."""

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from groups.access import member_for
from django.utils import timezone

from games import services as games
from games.access import session_for
from games.models import GameSession, Participant, SettingsPreset, Table
from groups.models import Invite, Member
from ledger import money
from ledger import queries as ledger_queries
from ledger import services as ledger


def home(request):
    memberships = (
        Member.objects.filter(user=request.user, status=Member.Status.ACTIVE)
        .select_related("group")
        .order_by("group__name")
    )
    return render(request, "web/home.html", {"memberships": memberships})


def group(request, group_id):
    me = member_for(request.user, group_id)
    members = Member.objects.filter(group=me.group, status=Member.Status.ACTIVE)
    context = {
        "me": me,
        "group": me.group,
        "members": members,
        "tables": Table.objects.filter(group=me.group, archived_at__isnull=True).select_related("default_preset"),
        "presets": SettingsPreset.objects.filter(group=me.group, archived_at__isnull=True),
    }
    sessions = GameSession.objects.filter(group=me.group).select_related("table")
    if not me.is_host:
        sessions = sessions.exclude(state=GameSession.State.SETUP)
    context["upcoming_sessions"] = [s for s in sessions if s.state in ("setup", "open", "running", "reconciliation")]
    context["past_sessions"] = [s for s in sessions if s.state in ("finalized", "canceled")]
    if me.is_host:
        context["invites"] = Invite.objects.filter(
            group=me.group, revoked_at__isnull=True, expires_at__gt=timezone.now()
        )
        context["new_invite_url"] = request.session.pop("new_invite_url", None)
    return render(request, "web/group.html", context)


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
        "default_buy_in": money.plain_pesos(current.default_buy_in_centavos),
        "summary": summary,
        "participants": participants,
        "my_participant": next((p for p in participants if p.member_id == me.pk), None),
        "my_line": next((line for line in summary.lines if line.participant.member_id == me.pk), None),
        "can_buy_in": me.is_host and session.state in ledger.BUY_IN_STATES,
        "can_reverse": me.is_host and session.state in ledger.REVERSAL_STATES,
        "can_cash_out": me.is_host and session.state in ledger.CASH_OUT_STATES,
        "balance": ledger_queries.balance(summary) if session.state == GameSession.State.RECONCILIATION else None,
        "seats_free": session.seat_count - seated,
        "can_join": session.state in games.JOINABLE_STATES,
        "can_manage_players": me.is_host and session.state in games.HOST_ADD_STATES,
    }
    if context["can_manage_players"]:
        present = {p.member_id for p in participants if p.status == Participant.Status.JOINED}
        context["addable_members"] = [
            m for m in Member.objects.filter(group_id=session.group_id, status=Member.Status.ACTIVE)
            if m.pk not in present
        ]
    return context


def session(request, session_id):
    session, me = session_for(request.user, session_id)
    return render(request, "web/session.html", session_context(session, me))


def session_state(request, session_id):
    """Polling endpoint: 204 while nothing changed, else a full snapshot of the live region."""
    session, me = session_for(request.user, session_id)
    if request.GET.get("v") == str(session.version):
        return HttpResponse(status=204)
    html = render_to_string("web/_session_live.html", session_context(session, me), request=request)
    return JsonResponse({"version": session.version, "html": html})
