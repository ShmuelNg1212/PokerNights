from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from . import services
from .access import member_for
from .errors import RuleError
from .http import attempt, attempt_bound, group_settings, keep_form
from .forms import GroupForm, NameForm
from .access import require_host
from .models import Member


@require_POST
def create_group(request):
    form = GroupForm(request.POST)
    member = attempt_bound(request, form, services.create_group, request.user, form.cleaned_data["name"]) if form.is_valid() else None
    if member is None:
        keep_form(request, "home:create", form)
        return redirect("home")
    return redirect("group", group_id=member.group_id)


@require_POST
def set_role(request, group_id, member_id):
    actor = member_for(request.user, group_id)
    attempt(request, services.set_role, actor, member_id, request.POST.get("role", ""), success="Role updated.")
    return group_settings(group_id, "players")


@require_POST
def remove_member(request, group_id, member_id):
    actor = member_for(request.user, group_id)
    attempt(request, services.remove_member, actor, member_id, success="Member removed.")
    return group_settings(group_id, "players")


@require_POST
def create_invite(request, group_id):
    actor = member_for(request.user, group_id)
    created = attempt(request, services.create_invite, actor)
    if created is not None:
        # Shown once on the next page; only the hash is stored.
        request.session["new_invite_url"] = request.build_absolute_uri(reverse("invite_accept", args=[created[1]]))
    return group_settings(group_id, "invites")


@require_POST
def revoke_invite(request, group_id, invite_id):
    actor = member_for(request.user, group_id)
    attempt(request, services.revoke_invite, actor, invite_id, success="Invite revoked.")
    return group_settings(group_id, "invites")


@login_not_required
def accept_invite(request, token):
    """The address in an invite link. A signed-out visitor is a newcomer: they go to sign-up."""
    try:
        invite = services.usable_invite(token)
    except RuleError as error:
        return render(request, "groups/invite_accept.html", {"error": str(error)}, status=404)
    if not request.user.is_authenticated:
        if request.method == "POST":
            return redirect_to_login(request.path)
        return redirect(f"{reverse('signup')}?{urlencode({'next': request.path})}")
    if request.method == "POST":
        member = attempt(request, services.accept_invite, request.user, token)
        if member is not None:
            messages.success(request, f"Welcome to {invite.group.name}. You're in.")
            return redirect("group", group_id=invite.group_id)
        return redirect("home")
    players = Member.objects.filter(group=invite.group, status=Member.Status.ACTIVE).count()
    return render(request, "groups/invite_accept.html", {"invite": invite, "players": players})


@require_POST
def add_roster_player(request, group_id):
    actor = member_for(request.user, group_id)
    require_host(actor)
    form = NameForm(request.POST, prefix=None)
    if not form.is_valid() or attempt_bound(request, form, services.add_roster_player, actor,
            form.cleaned_data["name"], request.POST.get("contact", ""), success="Player added.") is None:
        keep_form(request, f"{group_id}:add", form)
    return group_settings(group_id, "players")


@require_POST
def rename_member(request, group_id, member_id):
    actor = member_for(request.user, group_id)
    require_host(actor)
    form = NameForm(request.POST)
    if not form.is_valid() or attempt_bound(request, form, services.rename_member, actor, member_id,
            form.cleaned_data["name"], success="Player renamed.") is None:
        keep_form(request, f"{group_id}:rename:{member_id}", form)
    return group_settings(group_id, "players")
