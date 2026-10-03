from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from . import services
from .access import member_for
from .http import attempt


@require_POST
def create_group(request):
    member = attempt(request, services.create_group, request.user, request.POST.get("name", ""))
    if member is None:
        return redirect("home")
    return redirect("group", group_id=member.group_id)


@require_POST
def set_role(request, group_id, member_id):
    actor = member_for(request.user, group_id)
    attempt(request, services.set_role, actor, member_id, request.POST.get("role", ""), success="Role updated.")
    return redirect("group", group_id=group_id)


@require_POST
def remove_member(request, group_id, member_id):
    actor = member_for(request.user, group_id)
    attempt(request, services.remove_member, actor, member_id, success="Member removed.")
    return redirect("group", group_id=group_id)
