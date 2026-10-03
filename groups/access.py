"""Server-side access rules. Every view resolves objects through these helpers."""

from django.http import Http404

from .errors import NotAllowed
from .models import Member


def member_for(user, group_id) -> Member:
    """The requester's active membership in the group, or 404 so IDs do not leak."""
    member = (
        Member.objects.select_related("group")
        .filter(group_id=group_id, user=user, status=Member.Status.ACTIVE)
        .first()
    )
    if member is None:
        raise Http404("Not found")
    return member


def require_host(member: Member) -> None:
    if not member.is_host:
        raise NotAllowed("Only a host can do this.")
