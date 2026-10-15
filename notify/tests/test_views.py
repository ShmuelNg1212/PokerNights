import json

from django.test import TestCase
from django.urls import reverse

from groups.tests.helpers import make_user
from notify.models import PushSubscription
from notify.tests.helpers import phone_keys


def body(endpoint="https://push.example.com/send/abc"):
    p256dh, auth = phone_keys()
    return {"endpoint": endpoint, "expirationTime": None, "keys": {"p256dh": p256dh, "auth": auth}}


class SubscribeTests(TestCase):
    def setUp(self):
        self.user = make_user("ana")
        self.client.force_login(self.user)

    def post(self, name, data):
        return self.client.post(reverse(name), json.dumps(data), content_type="application/json")

    def test_subscribing_twice_saves_one_phone(self):
        data = body()
        self.assertEqual(self.post("alerts_subscribe", data).status_code, 204)
        self.assertEqual(self.post("alerts_subscribe", data).status_code, 204)
        self.assertEqual(PushSubscription.objects.filter(user=self.user).count(), 1)

    def test_a_phone_that_changes_hands_follows_the_new_login(self):
        data = body()
        self.post("alerts_subscribe", data)
        ben = make_user("ben")
        self.client.force_login(ben)
        self.post("alerts_subscribe", data)
        self.assertEqual(PushSubscription.objects.get().user, ben)

    def test_unsubscribing_removes_only_the_requesters_phone(self):
        data = body()
        self.post("alerts_subscribe", data)
        self.client.force_login(make_user("ben"))
        self.assertEqual(self.post("alerts_unsubscribe", {"endpoint": data["endpoint"]}).status_code, 204)
        self.assertEqual(PushSubscription.objects.count(), 1)  # ana's phone stays
        self.client.force_login(self.user)
        self.post("alerts_unsubscribe", {"endpoint": data["endpoint"]})
        self.assertEqual(PushSubscription.objects.count(), 0)

    def test_what_is_not_a_subscription_is_refused(self):
        for data in ({}, {"endpoint": "http://push.example.com/x", "keys": {"p256dh": "a", "auth": "b"}},
                     {"endpoint": "https://push.example.com/x", "keys": {"p256dh": "", "auth": "b"}},
                     {"endpoint": "https://push.example.com/x"}, ["x"]):
            self.assertEqual(self.post("alerts_subscribe", data).status_code, 400, data)
        self.assertEqual(self.client.post(reverse("alerts_subscribe"), "not json", content_type="application/json").status_code, 400)
        self.assertEqual(PushSubscription.objects.count(), 0)

    def test_a_get_is_not_allowed_and_a_visitor_must_log_in(self):
        self.assertEqual(self.client.get(reverse("alerts_subscribe")).status_code, 405)
        self.client.logout()
        response = self.post("alerts_subscribe", body())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PushSubscription.objects.count(), 0)

    def test_the_csrf_check_applies(self):
        from django.test import Client

        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.user)
        response = strict.post(reverse("alerts_subscribe"), json.dumps(body()), content_type="application/json")
        self.assertEqual(response.status_code, 403)
