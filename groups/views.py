from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from . import services
from .access import member_for
from .errors import RuleError
from .http import attempt, attempt_bound, group_settings, keep_form
from .forms import GroupForm, MemberForm, NameForm, NamesForm
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
def restore_member(request, group_id, member_id):
    actor = member_for(request.user, group_id)
    restored = attempt(request, services.restore_member, actor, member_id)
    if restored is not None:
        member, old = restored
        request.session["roster_arrived"] = [member.pk]
        if member.display_name == old:
            messages.success(request, f"{old} is back in the group.")
        else:
            messages.success(request, f"{old} is back as {member.display_name}, because another {old} is in the group. Rename either one.")
    return group_settings(group_id, "players")


@require_POST
def rename_self(request, group_id):
    actor = member_for(request.user, group_id)
    form = NameForm(request.POST)
    if not form.is_valid() or attempt_bound(request, form, services.rename_self, actor, form.cleaned_data["name"]) is None:
        keep_form(request, f"{group_id}:me", form)
    else:
        messages.success(request, f"Your name is now {' '.join(form.cleaned_data['name'].split())}.")
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


@require_POST
def create_password_reset(request, group_id, member_id):
    actor = member_for(request.user, group_id)
    created = attempt(request, services.create_password_reset, actor, member_id)
    if created is not None:
        member, link, token = created
        # Shown once on the next page; only the hash is stored.
        request.session["new_reset_link"] = {
            "name": member.display_name,
            "url": request.build_absolute_uri(reverse("password_reset", args=[token])),
            "expires_at": link.expires_at.isoformat(),
        }
    return group_settings(group_id, "players")


@require_POST
def cancel_password_reset(request, group_id, member_id):
    actor = member_for(request.user, group_id)
    attempt(request, services.cancel_password_reset, actor, member_id, success="Reset link cancelled.")
    return group_settings(group_id, "players")


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
    """One name per line. A form that sends ``name`` (the section with the roster tools off) adds that one."""
    actor = member_for(request.user, group_id)
    require_host(actor)
    several = "names" in request.POST or settings.ROSTER_TOOLS
    # A page drawn before the Names box existed still sends ``name``; its typing is kept in the box.
    data = request.POST if "names" in request.POST else {"names": request.POST.get("name", "")}
    form = NamesForm(data) if several else NameForm(request.POST, prefix=None)
    added = None
    if form.is_valid():
        names = form.cleaned_data["names"].splitlines() if several else [form.cleaned_data["name"]]
        added = attempt_bound(request, form, services.add_roster_players, actor, names)
    if added is None:
        keep_form(request, f"{group_id}:add", form)
    else:
        request.session["roster_arrived"] = [member.pk for member in added]  # the rows that are new on the next page
        messages.success(request, "Player added." if len(added) == 1 else f"Added {len(added)} players.")
    return group_settings(group_id, "players")


@require_POST
def rename_member(request, group_id, member_id):
    """Save a member's name, and the contact note when the form sends one."""
    actor = member_for(request.user, group_id)
    require_host(actor)
    detailed = "contact" in request.POST
    form = MemberForm(request.POST) if detailed else NameForm(request.POST)
    if not form.is_valid() or attempt_bound(
            request, form, services.edit_member, actor, member_id, form.cleaned_data["name"],
            form.cleaned_data["contact"] if detailed else None,
            success="Saved." if detailed else "Player renamed.") is None:
        keep_form(request, f"{group_id}:rename:{member_id}", form)
    return group_settings(group_id, "players")


@require_POST
def create_claim_link(request, group_id, member_id):
    actor = member_for(request.user, group_id)
    created = attempt(request, services.create_claim_link, actor, member_id)
    if created is not None:
        member, link, token = created
        # Shown once on the next page; only the hash is stored.
        request.session["new_claim_link"] = {
            "name": member.display_name,
            "url": request.build_absolute_uri(reverse("claim", args=[token])),
            "expires_at": link.expires_at.isoformat(),
        }
    return group_settings(group_id, "players")


@require_POST
def cancel_claim_link(request, group_id, member_id):
    actor = member_for(request.user, group_id)
    attempt(request, services.cancel_claim_link, actor, member_id, success="Claim link cancelled.")
    return group_settings(group_id, "players")


@login_not_required
@never_cache
def claim(request, token):
    """The address in a claim link. Opening it changes nothing; confirming makes the account that player."""
    response = _claim(request, token)
    # The address is a key to a player's place, so it is never passed on to another site. Not "no-referrer":
    # the browser would then send the form with "Origin: null" and the CSRF check would refuse it.
    response["Referrer-Policy"] = "same-origin"
    return response


def _claim(request, token):
    user = request.user if request.user.is_authenticated else None
    try:
        link = services.usable_claim_link(token, user=user)
    except RuleError as error:
        return render(request, "groups/claim.html", {"error": str(error)}, status=404)
    if user is None:
        if request.method == "POST":
            return redirect_to_login(request.path)
        return redirect(f"{reverse('signup')}?{urlencode({'next': request.path})}")
    preview = services.claim_preview(user, token)
    group = link.member.group
    if preview.done:
        return redirect("group", group_id=group.pk)
    if request.method == "POST" and not preview.refusal:
        member = attempt(request, services.claim_member, user, token)
        if member is not None:
            messages.success(request, f"Welcome to {group.name}. You're in as {member.display_name}.")
            return redirect("group", group_id=group.pk)
        return redirect("claim", token=token)
    return render(request, "groups/claim.html", {"group": group, "member": preview.member, "preview": preview, "one": [preview.member]})
