"""Server-side access rules. Every view resolves objects through these helpers."""

from django.http import Http404

from .errors import NotAllowed
from .models import Member


def member_for(user, group_id, *, archived=False) -> Member:
    """The requester's active membership in the group, or 404 so IDs do not leak.

    An archived group is not found, for hosts too. ``archived=True`` is for the
    few views that restore or delete it: they accept the group in either condition.
    """
    members = Member.objects.select_related("group").filter(group_id=group_id, user=user, status=Member.Status.ACTIVE)
    if not archived:
        members = members.filter(group__archived_at__isnull=True)
    member = members.first()
    if member is None:
        raise Http404("Not found")
    return member


def require_host(member: Member) -> None:
    if not member.is_host:
        raise NotAllowed("Only a host can do this.")


def _usable_invite_at(next_path: str):
    """The invite whose address is ``next_path`` if it can still be used, else None."""
    from urllib.parse import urlsplit

    from django.urls import Resolver404, resolve

    from . import services
    from .errors import RuleError

    try:
        match = resolve(urlsplit(next_path).path)
    except Resolver404:
        return None
    if match.url_name != "invite_accept":
        return None
    try:
        return services.usable_invite(match.kwargs["token"])
    except RuleError:
        return None


def invite_vouches(request, next_path: str) -> bool:
    """True when ``next_path`` is the address of an invite that can still be used."""
    return _usable_invite_at(next_path) is not None


def invite_group_name(request, next_path: str):
    """The group behind a usable invite address, for the entry pages. The link holder may know it."""
    invite = _usable_invite_at(next_path)
    return invite.group.name if invite else None
