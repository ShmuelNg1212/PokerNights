"""Session lookups that enforce group membership."""

import copy

from django.http import Http404

from groups.access import member_for

from groups.models import Member

from .models import GameNight, GameSession


def read_only(member):
    """A copy that renders as a player: the pages of an archived session offer no host action."""
    shown = copy.copy(member)
    shown.role = Member.Role.PLAYER
    return shown


def session_for(user, session_id) -> tuple[GameSession, object]:
    """``(session, member)`` for a requester in the session's group, or 404.

    A session in setup is a draft: only hosts can see it.
    """
    session = GameSession.objects.select_related("table", "group", "night").filter(pk=session_id).first()
    if session is None:
        raise Http404("Not found")
    member = member_for(user, session.group_id)
    if session.state == GameSession.State.SETUP and not member.is_host:
        raise Http404("Not found")
    return session, member


def night_for(user, night_id) -> tuple[GameNight, object]:
    """``(night, member)`` for a requester in the session's group, or 404.

    A session whose only sets are drafts is hidden from players.
    """
    night = GameNight.objects.select_related("table", "group").filter(pk=night_id).first()
    if night is None:
        raise Http404("Not found")
    member = member_for(user, night.group_id)
    if not member.is_host and not night.sets.exclude(state=GameSession.State.SETUP).exists():
        raise Http404("Not found")
    return night, member
