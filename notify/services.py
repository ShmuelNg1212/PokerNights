"""The only code allowed to write notices and subscriptions."""

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from . import push
from .models import Notice, PushSubscription


def tell(user_ids, *, group_id, session_id, kind, title, body, url, actor_name) -> list:
    """Tell each player, once per set, that they were put in it. Call inside the caller's transaction.

    Returns the ids of the users told now; a user told before about this set is skipped.
    The phone notifications go after the commit (``push.after_commit``).
    """
    if not (settings.TABLE_NOTICES or push.enabled()):
        return []
    wanted = list(dict.fromkeys(user_ids))
    told = set(
        Notice.objects.filter(session_id=session_id, night_id__isnull=True, user_id__in=wanted).values_list("user_id", flat=True)
    )
    new = [user_id for user_id in wanted if user_id not in told]
    Notice.objects.bulk_create(
        [Notice(user_id=user_id, group_id=group_id, session_id=session_id, kind=kind, title=title[:120],
                body=body[:255], url=url, actor_name=actor_name[:150]) for user_id in new],
        ignore_conflicts=True,
    )
    payload = {"title": title, "body": body, "url": url, "tag": f"set-{session_id}"}
    push.after_commit([(user_id, payload) for user_id in new])
    return new


def tell_night(user_ids, *, group_id, night_id, session_id, kind, title, body, url, actor_name) -> list:
    """An RSVP event of a session (``announced`` or ``seated``). Call inside the caller's transaction.

    An announcement reaches each user once. A move up is told each time it happens.
    """
    if not (settings.TABLE_NOTICES or push.enabled()):
        return []
    wanted = list(dict.fromkeys(user_ids))
    if kind == Notice.Kind.ANNOUNCED:
        told = set(Notice.objects.filter(night_id=night_id, kind=kind, user_id__in=wanted).values_list("user_id", flat=True))
        wanted = [user_id for user_id in wanted if user_id not in told]
    Notice.objects.bulk_create(
        [Notice(user_id=user_id, group_id=group_id, session_id=session_id, night_id=night_id, kind=kind,
                title=title[:120], body=body[:255], url=url, actor_name=actor_name[:150]) for user_id in wanted],
        ignore_conflicts=True,
    )
    payload = {"title": title, "body": body, "url": url, "tag": f"night-{night_id}"}
    push.after_commit([(user_id, payload) for user_id in wanted])
    return wanted


def unseen(user, session_ids) -> dict:
    """The viewer's set notices not yet looked at, for these sets: {session_id: notice}."""
    if not settings.TABLE_NOTICES or not session_ids:
        return {}
    notices = Notice.objects.filter(user=user, session_id__in=session_ids, night_id__isnull=True, seen_at__isnull=True)
    return {n.session_id: n for n in notices}


def mark_seen(user, session_id) -> None:
    """The player opened the set: its notice has done its job."""
    Notice.objects.filter(user=user, session_id=session_id, night_id__isnull=True, seen_at__isnull=True).update(
        seen_at=timezone.now()
    )


def mark_night_seen(user, night_id) -> None:
    """The player opened the session page: its RSVP notices have done their job."""
    Notice.objects.filter(user=user, night_id=night_id, seen_at__isnull=True).update(seen_at=timezone.now())


@transaction.atomic
def subscribe(user, endpoint, p256dh, auth) -> PushSubscription:
    """Save this phone for notifications. The endpoint is unique, so a second tap changes nothing,
    and a phone that changes hands (another login on it) moves to the new user."""
    subscription, _ = PushSubscription.objects.update_or_create(
        endpoint=endpoint, defaults={"user": user, "p256dh": p256dh, "auth": auth},
    )
    return subscription


def unsubscribe(user, endpoint) -> None:
    PushSubscription.objects.filter(user=user, endpoint=endpoint).delete()
