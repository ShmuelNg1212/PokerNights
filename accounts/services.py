"""The only code allowed to change accounts and password reset links."""

import hashlib
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
