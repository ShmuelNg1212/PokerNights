"""The only code allowed to change groups, members and invites."""

import hashlib
import secrets
from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.db.models.functions import Lower
from django.utils import timezone

from audit import services as audit

from .access import require_host
from .errors import RuleError
from .models import GameGroup, Invite, Member

NAME_MAX = 60
INVITE_DAYS = 7
INVITE_MAX_USES = 20


def clean_name(name: str, what="Name") -> str:
    name = " ".join((name or "").split())
    if not name:
        raise RuleError(f"{what} is required.")
    if len(name) > NAME_MAX:
        raise RuleError(f"{what} must be {NAME_MAX} characters or fewer.")
    return name


def _name_taken(group, name, *, exclude_pk=None) -> bool:
    taken = (
        Member.objects.filter(group=group, status=Member.Status.ACTIVE)
        .annotate(lower_name=Lower("display_name"))
        .filter(lower_name=name.lower())
    )
    if exclude_pk:
        taken = taken.exclude(pk=exclude_pk)
    return taken.exists()


def _free_name(group, name) -> str:
    """``name``, or ``name (2)`` and so on when an active member already uses it."""
    candidate, n = name, 1
    while _name_taken(group, candidate):
        n += 1
        candidate = f"{name[: NAME_MAX - 5]} ({n})"
    return candidate


def _lock_group(group_id) -> GameGroup:
    return GameGroup.objects.select_for_update().get(pk=group_id)


@transaction.atomic
def create_group(user, name: str) -> Member:
    """Create a group. Its creator is the first host."""
    group = GameGroup.objects.create(name=clean_name(name, "Group name"), created_by=user)
    member = Member.objects.create(
        group=group, user=user, display_name=user.get_username()[:NAME_MAX], role=Member.Role.HOST
    )
    audit.record("group.created", actor=user, group_id=group.pk, target=group, summary=f"Created group {group.name}")
    return member


def _active_host_count(group) -> int:
    return Member.objects.filter(group=group, role=Member.Role.HOST, status=Member.Status.ACTIVE).count()


@transaction.atomic
def set_role(actor: Member, member_id, role: str) -> Member:
    require_host(actor)
    if role not in Member.Role.values:
        raise RuleError("Unknown role.")
    group = _lock_group(actor.group_id)
    member = Member.objects.filter(group=group, pk=member_id, status=Member.Status.ACTIVE).first()
    if member is None:
        raise RuleError("That member is not in this group.")
    if member.role == role:
        return member
    if role == Member.Role.HOST and not member.has_login:
        raise RuleError("A player without a login cannot be a host.")
    if member.role == Member.Role.HOST and _active_host_count(group) <= 1:
        raise RuleError("A group needs at least one host.")
    member.role = role
    member.save(update_fields=["role"])
    audit.record(
        "member.role_changed", actor=actor.user, group_id=group.pk, target=member,
        summary=f"{member.display_name} is now a {role}",
    )
    return member


@transaction.atomic
def remove_member(actor: Member, member_id) -> Member:
    require_host(actor)
    group = _lock_group(actor.group_id)
    member = Member.objects.filter(group=group, pk=member_id, status=Member.Status.ACTIVE).first()
    if member is None:
        raise RuleError("That member is not in this group.")
    if member.role == Member.Role.HOST and _active_host_count(group) <= 1:
        raise RuleError("A group needs at least one host.")
    member.status = Member.Status.REMOVED
    member.save(update_fields=["status"])
    audit.record(
        "member.removed", actor=actor.user, group_id=group.pk, target=member,
        summary=f"Removed {member.display_name} from the group",
    )
    return member


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@transaction.atomic
def create_invite(actor: Member) -> tuple[Invite, str]:
    """Create an invite. The token is returned once and is not stored."""
    require_host(actor)
    token = secrets.token_urlsafe(32)
    invite = Invite.objects.create(
        group=actor.group,
        token_hash=hash_token(token),
        expires_at=timezone.now() + timedelta(days=INVITE_DAYS),
        max_uses=INVITE_MAX_USES,
        created_by=actor.user,
    )
    audit.record("invite.created", actor=actor.user, group_id=actor.group_id, target=invite, summary="Created an invite link")
    return invite, token


@transaction.atomic
def revoke_invite(actor: Member, invite_id) -> Invite:
    require_host(actor)
    invite = Invite.objects.select_for_update().filter(group=actor.group, pk=invite_id).first()
    if invite is None:
        raise RuleError("That invite is not in this group.")
    if invite.revoked_at is None:
        invite.revoked_at = timezone.now()
        invite.save(update_fields=["revoked_at"])
        audit.record("invite.revoked", actor=actor.user, group_id=actor.group_id, target=invite, summary="Revoked an invite link")
    return invite


def usable_invite(token: str, *, lock=False) -> Invite:
    """The invite for ``token`` if it can still be used, else RuleError."""
    invites = Invite.objects.select_related("group")
    if lock:
        invites = Invite.objects.select_for_update()
    invite = invites.filter(token_hash=hash_token(token or "")).first()
    if invite is None or invite.revoked_at is not None:
        raise RuleError("This invite link is not valid.")
    if invite.expires_at <= timezone.now():
        raise RuleError("This invite link has expired. Ask a host for a new one.")
    if invite.use_count >= invite.max_uses:
        raise RuleError("This invite link has been used up. Ask a host for a new one.")
    return invite


@transaction.atomic
def accept_invite(user, token: str) -> Member:
    """Make ``user`` a player in the invite's group. Accepting again changes nothing."""
    invite = usable_invite(token, lock=True)
    group = _lock_group(invite.group_id)
    member = Member.objects.filter(group=group, user=user).first()
    if member is not None and member.status == Member.Status.ACTIVE:
        return member
    if member is not None:
        member.display_name = _free_name(group, member.display_name)
        member.status = Member.Status.ACTIVE
        member.role = Member.Role.PLAYER
        member.save(update_fields=["display_name", "status", "role"])
    else:
        member = Member.objects.create(
            group=group, user=user, display_name=_free_name(group, user.get_username()[:NAME_MAX])
        )
    Invite.objects.filter(pk=invite.pk).update(use_count=F("use_count") + 1)
    audit.record("invite.accepted", actor=user, group_id=group.pk, target=member, summary=f"{member.display_name} joined the group")
    return member
