"""Pages that compose several apps. They only read; each write is a POST view in its own app."""

from django.shortcuts import render

from groups.access import member_for
from groups.models import Member


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
    return render(request, "web/group.html", {"me": me, "group": me.group, "members": members})
