"""Session lookups that enforce group membership."""

from django.http import Http404

from groups.access import member_for

from .models import GameSession


def session_for(user, session_id) -> tuple[GameSession, object]:
    """``(session, member)`` for a requester in the session's group, or 404.

    A session in setup is a draft: only hosts can see it.
    """
    session = GameSession.objects.select_related("table", "group").filter(pk=session_id).first()
    if session is None:
        raise Http404("Not found")
    member = member_for(user, session.group_id)
    if session.state == GameSession.State.SETUP and not member.is_host:
        raise Http404("Not found")
    return session, member
