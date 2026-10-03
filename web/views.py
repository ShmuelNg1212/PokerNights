"""Pages that compose several apps. They only read; each write is a POST view in its own app."""

from django.shortcuts import render

from groups.access import member_for
from django.utils import timezone

from games import services as games
from games.access import session_for
from games.models import GameSession, SettingsPreset, Table
from groups.models import Invite, Member


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


def session(request, session_id):
    session, me = session_for(request.user, session_id)
    context = {"session": session, "me": me, "settings": games.current_settings(session)}
    return render(request, "web/session.html", context)
