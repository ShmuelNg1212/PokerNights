"""The only code allowed to change groups, members and invites."""

import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.db.models.functions import Lower
from django.utils import timezone

from accounts import services as accounts
from audit import services as audit

from .access import require_host
from .errors import RuleError
from .models import GameGroup, GroupRakeAccount, Invite, Member

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


GROUP_ARCHIVED = "This group is archived. A host can restore it from Your groups."


def lock_group(group_id, *, allow_archived=False) -> GameGroup:
    """The group row, locked for the rest of the transaction. An archived group takes no write."""
    group = GameGroup.objects.select_for_update().get(pk=group_id)
    if group.is_archived and not allow_archived:
        raise RuleError(GROUP_ARCHIVED)
    return group


_lock_group = lock_group

# Reasons a group cannot be archived yet. An app that knows about play registers a guard:
# guard(group) raises RuleError. This app does not import the apps that depend on it.
ARCHIVE_GUARDS = []


@transaction.atomic
def archive_group(actor: Member) -> GameGroup:
    """Hide the group from every member. Nothing is removed; a host can restore it."""
    require_host(actor)
    group = lock_group(actor.group_id, allow_archived=True)
    if group.is_archived:
        return group  # a repeated tap
    for guard in ARCHIVE_GUARDS:
        guard(group)
    group.archived_at, group.archived_by = timezone.now(), actor.user
    group.save(update_fields=["archived_at", "archived_by"])
    audit.record("group.archived", actor=actor.user, group_id=group.pk, target=group, summary=f"Archived group {group.name}")
    return group


@transaction.atomic
def restore_group(actor: Member) -> GameGroup:
    require_host(actor)
    group = lock_group(actor.group_id, allow_archived=True)
    if not group.is_archived:
        return group  # a repeated tap
    group.archived_at = group.archived_by = None
    group.save(update_fields=["archived_at", "archived_by"])
    audit.record("group.restored", actor=actor.user, group_id=group.pk, target=group, summary=f"Restored group {group.name}")
    return group


@transaction.atomic
def create_group(user, name: str) -> Member:
    """Create a group. Its creator is the first host."""
    group = GameGroup.objects.create(name=clean_name(name, "Group name"), created_by=user)
    GroupRakeAccount.objects.create(group=group)
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
        raise RuleError(LAST_HOST)
    member.role = role
    member.save(update_fields=["role"])
    audit.record(
        "member.role_changed", actor=actor.user, group_id=group.pk, target=member,
        summary=f"{member.display_name} is now a {role}",
    )
    return member


# Reasons a member cannot be removed yet. An app that knows about play registers a guard:
# guard(member) raises RuleError. This app does not import the apps that depend on it.
REMOVE_GUARDS = []

LAST_HOST = "A group needs at least one host. Make someone else a host first."
TURNED_OFF = "This is turned off."
NOT_IN_GROUP = "That member is not in this group."


def _removal_block(group, member) -> str | None:
    """Why an active member cannot be removed now, or None."""
    if member.role == Member.Role.HOST and _active_host_count(group) <= 1:
        return LAST_HOST
    for guard in REMOVE_GUARDS:
        try:
            guard(member)
        except RuleError as error:
            return str(error)
    return None


def removal_refusal(actor: Member, member_id) -> str | None:
    """The reason removing this member would be refused, for the page that asks first. Changes nothing."""
    require_host(actor)
    member = Member.objects.filter(group_id=actor.group_id, pk=member_id, status=Member.Status.ACTIVE).first()
    if member is None:
        raise RuleError(NOT_IN_GROUP)
    return _removal_block(actor.group, member)


@transaction.atomic
def remove_member(actor: Member, member_id) -> Member:
    """Take a member off the roster. Their records stay theirs, and a host can bring them back."""
    require_host(actor)
    group = _lock_group(actor.group_id)
    # The member row is locked so that seating the same member waits for this, and this for it.
    member = Member.objects.select_for_update().filter(group=group, pk=member_id).first()
    if member is None:
        raise RuleError(NOT_IN_GROUP)
    if member.status == Member.Status.REMOVED:
        return member  # a repeated tap
    block = _removal_block(group, member)
    if block:
        raise RuleError(block)
    member.status = Member.Status.REMOVED
    member.save(update_fields=["status"])
    audit.record(
        "member.removed", actor=actor.user, group_id=group.pk, target=member,
        summary=f"Removed {member.display_name} from the group",
    )
    return member


@transaction.atomic
def restore_member(actor: Member, member_id) -> tuple[Member, str]:
    """Bring a removed member back as a player. Returns (member, the name they had).

    The row is the same one, so every past result is still theirs. A name another active
    player took meanwhile is settled here, before the row turns active.
    """
    require_host(actor)
    if not settings.ROSTER_TOOLS:
        raise RuleError(TURNED_OFF)
    group = _lock_group(actor.group_id)
    member = Member.objects.select_for_update().filter(group=group, pk=member_id).first()
    if member is None:
        raise RuleError(NOT_IN_GROUP)
    old = member.display_name
    if member.status == Member.Status.ACTIVE:
        return member, old  # a repeated tap
    member.display_name = _free_name(group, old)
    member.status = Member.Status.ACTIVE
    member.role = Member.Role.PLAYER
    member.save(update_fields=["display_name", "status", "role"])
    audit.record(
        "member.restored", actor=actor.user, group_id=group.pk, target=member,
        summary=f"Brought {member.display_name} back to the group",
    )
    return member, old


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@transaction.atomic
def create_invite(actor: Member) -> tuple[Invite, str]:
    """Create an invite. The token is returned once and is not stored."""
    require_host(actor)
    lock_group(actor.group_id)
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
    if invite is None or invite.revoked_at is not None or invite.group.is_archived:
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


def _reset_target(actor: Member, member_id) -> Member:
    """The member a host may manage a password reset link for, with the group row locked."""
    require_host(actor)
    group = _lock_group(actor.group_id)
    member = Member.objects.select_related("user").filter(group=group, pk=member_id, status=Member.Status.ACTIVE).first()
    if member is None:
        raise RuleError("That member is not in this group.")
    if member.pk == actor.pk:
        raise RuleError("This is for another player.")
    if not member.has_login:
        raise RuleError(f"{member.display_name} has no login.")
    return member


@transaction.atomic
def create_password_reset(actor: Member, member_id):
    """Create a reset link for a member's account. Returns (member, link, token); the token is shown once.

    The link lets its holder become the account, so it is refused for anyone whose account
    reaches further than this group's host already does: the admin, or another group's host powers.
    """
    if not settings.RESET_LINKS:
        raise RuleError("Password reset links are turned off.")
    member = _reset_target(actor, member_id)
    if member.user.is_staff or member.user.is_superuser:
        raise RuleError("A site administrator's password is set in the admin.")
    hosts_elsewhere = Member.objects.filter(
        user=member.user, role=Member.Role.HOST, status=Member.Status.ACTIVE
    ).exclude(group_id=member.group_id)
    if hosts_elsewhere.exists():
        raise RuleError(f"{member.display_name} hosts another group. The site administrator resets their password.")
    link, token = accounts.issue_reset_link(member.user, created_by=actor.user, group_id=member.group_id)
    audit.record(
        "password_reset.issued", actor=actor.user, group_id=member.group_id, target=member,
        summary=f"Created a password reset link for {member.display_name}",
    )
    return member, link, token


@transaction.atomic
def cancel_password_reset(actor: Member, member_id) -> Member:
    member = _reset_target(actor, member_id)
    if accounts.revoke_reset_links(member.user):
        audit.record(
            "password_reset.cancelled", actor=actor.user, group_id=member.group_id, target=member,
            summary=f"Cancelled the password reset link for {member.display_name}",
        )
    return member


CONTACT_MAX = 120
ADD_MAX = 30
REMOVED_NAME = "Removed from this group: {names}. Bring them back from Removed players, or use a different name."


def _removed_names(group) -> set:
    """Lower-case names of removed members. Adding one again would split that person's history."""
    if not settings.ROSTER_TOOLS:
        return set()
    return {name.lower() for name in Member.objects.filter(group=group, status=Member.Status.REMOVED).values_list("display_name", flat=True)}


def _create_roster_player(actor, group, name, contact="") -> Member:
    member = Member.objects.create(group=group, display_name=name, contact=contact)
    audit.record("member.added", actor=actor.user, group_id=group.pk, target=member, summary=f"Added {name} to the roster")
    return member


@transaction.atomic
def add_roster_player(actor: Member, name: str, contact: str = "") -> Member:
    """Add a player who has no login. A host acts for this player."""
    require_host(actor)
    group = _lock_group(actor.group_id)
    name = clean_name(name, "Player name")
    if _name_taken(group, name):
        raise RuleError(f"A player named {name} is already in this group.")
    if name.lower() in _removed_names(group):
        raise RuleError(REMOVED_NAME.format(names=name))
    return _create_roster_player(actor, group, name, (contact or "").strip()[:CONTACT_MAX])


@transaction.atomic
def add_roster_players(actor: Member, names) -> list:
    """Add several players without logins. Everyone is added, or nobody is; every problem is named at once."""
    require_host(actor)
    typed = [" ".join((name or "").split()) for name in names]
    typed = [name for name in typed if name]
    if not typed:
        raise RuleError("Type at least one name.")
    if len(typed) == 1:
        return [add_roster_player(actor, typed[0])]
    if not settings.ROSTER_TOOLS:
        raise RuleError(TURNED_OFF)
    if len(typed) > ADD_MAX:
        raise RuleError(f"Add {ADD_MAX} players at most at a time.")
    group = _lock_group(actor.group_id)
    active = {name.lower() for name in Member.objects.filter(group=group, status=Member.Status.ACTIVE).values_list("display_name", flat=True)}
    removed = _removed_names(group)
    taken, twice, gone, long, seen = [], [], [], [], set()
    for name in typed:
        key = name.lower()
        if len(name) > NAME_MAX:
            long.append(f"{name[:20]}…")
        elif key in seen:
            twice.append(name)
        elif key in active:
            taken.append(name)
        elif key in removed:
            gone.append(name)
        seen.add(key)
    problems = []
    if taken:
        problems.append(f"Already in this group: {', '.join(taken)}.")
    if twice:
        problems.append(f"Typed twice: {', '.join(twice)}.")
    if gone:
        problems.append(REMOVED_NAME.format(names=", ".join(gone)))
    if long:
        problems.append(f"Too long ({NAME_MAX} characters at most): {', '.join(long)}")
    if problems:
        raise RuleError(" ".join(problems))
    return [_create_roster_player(actor, group, name) for name in typed]


def _rename(actor, group, member, name) -> bool:
    """Give ``member`` a cleaned ``name`` under the group lock. False when it is the name they have."""
    if _name_taken(group, name, exclude_pk=member.pk):
        raise RuleError(f"A player named {name} is already in this group.")
    old = member.display_name
    if old == name:
        return False
    member.display_name = name
    member.save(update_fields=["display_name"])
    audit.record("member.renamed", actor=actor.user, group_id=group.pk, target=member, summary=f"Renamed {old} to {name}")
    return True


@transaction.atomic
def edit_member(actor: Member, member_id, name: str, contact: str | None = None) -> Member:
    """A host changes a member's name, and the contact note when one is given. Only what changed is written.

    The contact note is a host's note about a person. Its text is kept out of the audit log.
    """
    require_host(actor)
    group = _lock_group(actor.group_id)
    member = Member.objects.filter(group=group, pk=member_id, status=Member.Status.ACTIVE).first()
    if member is None:
        raise RuleError(NOT_IN_GROUP)
    name = clean_name(name, "Player name")
    if contact is not None:
        contact = " ".join(contact.split())
        if len(contact) > CONTACT_MAX:
            raise RuleError(f"Contact must be {CONTACT_MAX} characters or fewer.")
        if contact != member.contact and not settings.ROSTER_TOOLS:
            raise RuleError(TURNED_OFF)
    _rename(actor, group, member, name)
    if contact is not None and contact != member.contact:
        member.contact = contact
        member.save(update_fields=["contact"])
        audit.record(
            "member.contact_changed", actor=actor.user, group_id=group.pk, target=member,
            summary=f"Changed {member.display_name}'s contact note",
        )
    return member


def rename_member(actor: Member, member_id, name: str) -> Member:
    return edit_member(actor, member_id, name)


@transaction.atomic
def rename_self(actor: Member, name: str) -> Member:
    """Anyone changes their own name in the group. The username they log in with is another thing."""
    if not settings.ROSTER_TOOLS:
        raise RuleError(TURNED_OFF)
    group = _lock_group(actor.group_id)
    member = Member.objects.filter(group=group, pk=actor.pk, status=Member.Status.ACTIVE).first()
    if member is None:
        raise RuleError(NOT_IN_GROUP)
    _rename(actor, group, member, clean_name(name))
    return member
