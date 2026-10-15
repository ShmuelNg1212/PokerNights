import json
from unittest import mock

from django.test import TestCase, override_settings

from groups.tests.helpers import make_user
from notify import push, services
from notify.models import PushSubscription
from notify.tests.helpers import phone_keys, vapid_private_key
from notify.tests.test_notices import Table

KEYS = {"VAPID_PUBLIC_KEY": "public", "VAPID_SUBJECT": "https://pokernights-five.vercel.app", "PUSH_ALERTS": True}


def subscribe(user, n=1):
    p256dh, auth = phone_keys()
    return services.subscribe(user, f"https://push.example.com/send/{user.pk}-{n}", p256dh, auth)


class Answer:
    def __init__(self, status):
        self.status_code, self.text, self.headers = status, "", {}


@override_settings(VAPID_PRIVATE_KEY="", **{k: v for k, v in KEYS.items()})
class SendingTests(TestCase):
    def setUp(self):
        self.key = vapid_private_key()

    def test_opening_sends_after_the_commit_with_the_notice_words(self):
        table = Table()
        ana = table.player("ana")
        subscribe(ana.user)
        table.add(ana)
        with override_settings(VAPID_PRIVATE_KEY=self.key), mock.patch("pywebpush.webpush") as webpush:
            with self.captureOnCommitCallbacks(execute=False) as callbacks:
                table.open()
            webpush.assert_not_called()  # nothing before the commit
            for callback in callbacks:
                callback()
        webpush.assert_called_once()
        call = webpush.call_args.kwargs
        self.assertEqual(json.loads(call["data"]), {
            "title": "Friday table · set 1 is open", "body": "hana added you. Tap to see the table.",
            "url": f"/s/{table.session.pk}/", "tag": f"set-{table.session.pk}",
        })
        self.assertEqual(call["vapid_claims"], {"sub": "https://pokernights-five.vercel.app"})
        self.assertEqual((call["timeout"], call["ttl"]), (5, 6 * 60 * 60))
        self.assertEqual(call["headers"], {"Urgency": "high", "Topic": f"set-{table.session.pk}"})
        self.assertIsNotNone(PushSubscription.objects.get().last_sent_at)

    def test_without_the_private_key_nothing_is_sent(self):
        table = Table()
        ana = table.player("ana")
        subscribe(ana.user)
        table.add(ana)
        with mock.patch("pywebpush.webpush") as webpush, self.captureOnCommitCallbacks(execute=True):
            table.open()
        webpush.assert_not_called()

    def test_a_rollback_sends_nothing(self):
        from django.db import transaction

        table = Table()
        ana = table.player("ana")
        subscribe(ana.user)
        table.add(ana)
        with override_settings(VAPID_PRIVATE_KEY=self.key), mock.patch("pywebpush.webpush") as webpush:
            with self.captureOnCommitCallbacks(execute=True):
                try:
                    with transaction.atomic():
                        table.open()
                        raise RuntimeError("undo")
                except RuntimeError:
                    pass
        webpush.assert_not_called()

    def test_every_phone_of_the_player_is_sent_to(self):
        user = make_user("ana")
        subscribe(user, 1), subscribe(user, 2)
        with override_settings(VAPID_PRIVATE_KEY=self.key), mock.patch("pywebpush.webpush") as webpush:
            push.send([(user.pk, {"title": "t", "body": "b", "url": "/", "tag": "set-1"})])
        self.assertEqual(webpush.call_count, 2)

    def test_a_forgotten_phone_is_removed_and_a_failing_one_kept(self):
        from pywebpush import WebPushException

        gone, failing = make_user("gone"), make_user("failing")
        subscribe(gone), subscribe(failing)

        def answer(subscription_info, **kwargs):
            status = 410 if "/%d-" % gone.pk in subscription_info["endpoint"] else 500
            raise WebPushException("refused", response=Answer(status))

        with override_settings(VAPID_PRIVATE_KEY=self.key), mock.patch("pywebpush.webpush", side_effect=answer):
            push.send([(gone.pk, {"tag": "set-1"}), (failing.pk, {"tag": "set-1"})])
        self.assertEqual(list(PushSubscription.objects.values_list("user__username", flat=True)), ["failing"])

    def test_a_timeout_never_reaches_the_host(self):
        table = Table()
        ana = table.player("ana")
        subscribe(ana.user)
        table.add(ana)
        with override_settings(VAPID_PRIVATE_KEY=self.key), mock.patch("pywebpush.webpush", side_effect=TimeoutError):
            with self.assertLogs("notify.push", "ERROR"), self.captureOnCommitCallbacks(execute=True):
                table.open()
        self.assertEqual(table.session.state, "open")
        self.assertEqual(PushSubscription.objects.count(), 1)

    def test_a_real_message_is_encrypted_signed_and_posted_to_the_push_service(self):
        """No mock of pywebpush: our key format and arguments must be what it accepts."""
        user = make_user("ana")
        sub = subscribe(user)
        with override_settings(VAPID_PRIVATE_KEY=self.key), mock.patch("requests.post", return_value=Answer(201)) as post:
            self.assertEqual(push.deliver(sub, {"title": "t", "body": "b", "url": "/", "tag": "set-1"}), "sent")
        url, kwargs = post.call_args.args[0], post.call_args.kwargs
        self.assertEqual(url, sub.endpoint)
        self.assertEqual(kwargs["headers"]["content-encoding"], "aes128gcm")
        self.assertTrue(kwargs["headers"]["authorization"].startswith("vapid t="))
        self.assertEqual((kwargs["headers"]["ttl"], kwargs["headers"]["Topic"]), ("21600", "set-1"))
        self.assertNotIn(b'"title"', kwargs["data"])  # the payload is encrypted
