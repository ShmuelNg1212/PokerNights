"""The only code allowed to change accounts and password reset links."""

import hashlib
import math
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from audit import services as audit

from .models import PasswordResetLink, User

RESET_HOURS = 24

NOT_VALID = "This reset link is not valid."


class ResetLinkError(Exception):
    """A reset link that cannot be used. The message is shown to the person who opened it."""


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _live(links):
    return links.filter(used_at__isnull=True, revoked_at__isnull=True, expires_at__gt=timezone.now())


def live_reset_links(user_ids) -> dict:
    """The link that can still be used, by user id, for the users that have one. Read-only."""
    if not settings.RESET_LINKS:
        return {}
    return {link.user_id: link for link in _live(PasswordResetLink.objects.filter(user_id__in=user_ids))}


@transaction.atomic
def issue_reset_link(user, *, created_by, group_id=None) -> tuple[PasswordResetLink, str]:
    """Create the user's one live reset link. The token is returned once and is not stored.

    The caller decides who may ask and records the audit event.
    """
    User.objects.select_for_update().get(pk=user.pk)
    # The earlier link is cancelled first, so an account never has two live ones.
    _live(PasswordResetLink.objects.filter(user=user)).update(revoked_at=timezone.now())
    token = secrets.token_urlsafe(32)
    link = PasswordResetLink.objects.create(
        user=user,
        token_hash=hash_token(token),
        expires_at=timezone.now() + timedelta(hours=RESET_HOURS),
        created_by=created_by,
        group_id=group_id,
    )
    return link, token


@transaction.atomic
def revoke_reset_links(user) -> int:
    """Cancel the user's live links. Returns how many there were; the caller records the audit event."""
    User.objects.select_for_update().get(pk=user.pk)
    return _live(PasswordResetLink.objects.filter(user=user)).update(revoked_at=timezone.now())


def usable_reset_link(token: str, *, lock=False) -> PasswordResetLink:
    """The link for ``token`` if it can still be used, else ResetLinkError."""
    links = PasswordResetLink.objects.select_for_update() if lock else PasswordResetLink.objects.select_related("user")
    link = links.filter(token_hash=hash_token(token or "")).first()
    if not settings.RESET_LINKS or link is None or link.revoked_at is not None or not link.user.is_active:
        raise ResetLinkError(NOT_VALID)
    if link.used_at is not None:
        raise ResetLinkError("This reset link has already been used.")
    if link.expires_at <= timezone.now():
        raise ResetLinkError("This reset link has expired.")
    return link


@transaction.atomic
def redeem_reset_link(token: str, password: str) -> User:
    """Set the new password and use the link up. Every other login of the account ends."""
    link = usable_reset_link(token, lock=True)
    user = User.objects.select_for_update().get(pk=link.user_id)
    user.set_password(password)
    user.save(update_fields=["password"])
    link.used_at = timezone.now()
    link.save(update_fields=["used_at"])
    audit.record(
        "password.reset", actor=user, group_id=link.group_id, target=user,
        summary=f"{user.get_username()} set a new password from a reset link",
    )
    return user


CHANGE_TRIES = 5
CHANGE_MINUTES = 15


class PasswordChangeError(Exception):
    pass


def _refused_since(user, since):
    from audit.models import AuditEvent

    return AuditEvent.objects.filter(action="password.change_refused", actor=user, created_at__gt=since)


@transaction.atomic
def _change(user, current: str, new: str) -> str:
    """The change itself, or the reason it was refused. A refusal is still written, so it is counted."""
    user = User.objects.select_for_update().get(pk=user.pk)
    since = timezone.now() - timedelta(minutes=CHANGE_MINUTES)
    refused = _refused_since(user, since)
    if refused.count() >= CHANGE_TRIES:
        oldest = refused.order_by("created_at").values_list("created_at", flat=True)[0]
        wait = max(1, math.ceil((oldest - since).total_seconds() / 60))
        return f"Too many wrong passwords. Try again in {wait} minute{'' if wait == 1 else 's'}."
    if not user.check_password(current):
        if user.check_password(new):
            return ""  # the same change sent twice: the first one already made it
        audit.record("password.change_refused", actor=user, target=user,
                     summary=f"{user.get_username()} gave a wrong current password")
        return "That is not your current password."
    user.set_password(new)
    user.save(update_fields=["password"])
    revoke_reset_links(user)
    audit.record("password.changed", actor=user, target=user, summary=f"{user.get_username()} changed their password")
    return ""


def change_password(user, current: str, new: str) -> User:
    """A person sets a new password, giving the current one. Live reset links stop working.

    After ``CHANGE_TRIES`` wrong current passwords in ``CHANGE_MINUTES`` minutes, every try is refused
    until the oldest of them is that old. The caller keeps the login with ``update_session_auth_hash``;
    the account's other logins end.
    """
    refused = _change(user, current, new)
    if refused:
        raise PasswordChangeError(refused)
    user.refresh_from_db(fields=["password"])
    return user
