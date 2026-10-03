"""Pages that compose several apps. They only read; each write is a POST view in its own app."""

from django.shortcuts import render

from groups.access import member_for
from django.utils import timezone

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
    context = {"me": me, "group": me.group, "members": members}
    if me.is_host:
        context["invites"] = Invite.objects.filter(
            group=me.group, revoked_at__isnull=True, expires_at__gt=timezone.now()
        )
        context["new_invite_url"] = request.session.pop("new_invite_url", None)
    return render(request, "web/group.html", context)
