"""The only code allowed to change groups, members and invites."""

from django.db import transaction
from django.db.models.functions import Lower

from audit import services as audit

from .access import require_host
from .errors import RuleError
from .models import GameGroup, Member

NAME_MAX = 60


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
