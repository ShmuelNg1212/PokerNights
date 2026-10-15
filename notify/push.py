"""Phone notifications by Web Push, sent after the transaction that told the player commits.

Each message is encrypted for the phone and signed with the VAPID key pair; ``VAPID_SUBJECT``
is the contact the push services may use about our messages. The sends run in parallel,
each with a time limit, in the request that told the player: there is no queue. A failure
is logged and dropped, never raised: the set is open whether or not a phone was reached.
A push service that answers 404 or 410 has forgotten the phone, so its subscription goes.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.db import transaction
from django.utils import timezone

log = logging.getLogger(__name__)

TIMEOUT = 5          # seconds per phone
TTL = 6 * 60 * 60    # a phone that is off for longer than this gets nothing
WORKERS = 8
GONE = (404, 410)


def enabled() -> bool:
    return bool(settings.PUSH_ALERTS and settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY)


def after_commit(messages) -> None:
    """``messages``: (user_id, payload) pairs. Sent once the caller's transaction commits; nothing on a rollback."""
    if messages and enabled():
        transaction.on_commit(lambda: send(messages))


def send(messages) -> None:
    from .models import PushSubscription

    payloads = dict(messages)
    subscriptions = list(PushSubscription.objects.filter(user_id__in=payloads))
    if not subscriptions:
        return
    with ThreadPoolExecutor(max_workers=min(WORKERS, len(subscriptions))) as pool:
        results = list(pool.map(lambda sub: deliver(sub, payloads[sub.user_id]), subscriptions))
    gone = [sub.pk for sub, result in zip(subscriptions, results) if result == "gone"]
    sent = [sub.pk for sub, result in zip(subscriptions, results) if result == "sent"]
    if gone:
        PushSubscription.objects.filter(pk__in=gone).delete()
    if sent:
        PushSubscription.objects.filter(pk__in=sent).update(last_sent_at=timezone.now())


def deliver(subscription, payload) -> str:
    """One phone: "sent", "gone" (forget it) or "failed" (keep it, try next time)."""
    from pywebpush import WebPushException, webpush

    try:
        webpush(
            subscription_info={"endpoint": subscription.endpoint, "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth}},
            data=json.dumps(payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_SUBJECT},  # a new dict each time: webpush writes into it
            ttl=TTL,
            timeout=TIMEOUT,
            headers={"Urgency": "high", "Topic": payload["tag"]},
        )
        return "sent"
    except WebPushException as error:
        status = getattr(error.response, "status_code", None)
        if status in GONE:
            return "gone"
        log.warning("push to subscription %s failed: %s", subscription.pk, status or error)
    except Exception:  # a timeout, a refused connection, a bad key: never the host's problem
        log.exception("push to subscription %s failed", subscription.pk)
    return "failed"
