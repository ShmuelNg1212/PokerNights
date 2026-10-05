"""An action sent in place is answered with its page in one request, when the form asks for it (config/inplace.py)."""

import re
import uuid
from unittest import mock

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ledger.models import BuyIn
from ledger.tests.helpers import Night
from settlement.models import Payment, Transfer
from settlement.tests.test_archive import closed_example


class OneTripTests(TestCase):
    def setUp(self):
        self.night = Night("A", "B")
        self.page = reverse("session", args=[self.night.session.pk])
        self.add = reverse("buy_in_add", args=[self.night.session.pk])
        self.client.force_login(self.night.host.user)

    def buy(self, amount="1000", client=None, page=None, **extra):
        data = {"participant_id": self.night.players["A"].pk, "amount": amount, "request_id": uuid.uuid4(), **extra}
        headers = {} if page is False else {"HTTP_X_ANSWER_IN_PLACE": page or self.page}
        return (client or self.client).post(self.add, data, **headers)

    def test_the_post_is_answered_with_the_updated_page(self):
        answer = self.buy()
        self.assertEqual(answer.status_code, 200)
        self.assertEqual(answer["X-In-Place-Location"], self.page)
        self.assertIn("no-store", answer["Cache-Control"])
        self.assertEqual(BuyIn.objects.count(), 1)
        html = answer.content.decode()
        self.assertIn('data-method="GET"', html)  # the page reports itself as an ordinary page view
        self.assertIn("₱1,000", html)
        self.assertIn('id="live"', html)
        self.assertEqual(html, re.sub(r"\s+$", "", html) + html[len(html.rstrip()):])  # a whole document
        self.assertTrue(html.lstrip().lower().startswith("<!doctype html>"))

    def test_it_is_the_same_page_a_browser_would_fetch_after_the_redirect(self):
        def clean(html):
            html = re.sub(r'name="csrfmiddlewaretoken" value="[^"]+"', "CSRF", html)
            return re.sub(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "UUID", html)

        bought = self.night.buy("A", 1000)
        answered = self.client.post(
            reverse("buy_in_reverse", args=[self.night.session.pk, bought.pk]), {"reason": "duplicate"},
            HTTP_X_ANSWER_IN_PLACE=self.page,
        ).content.decode()
        fetched = self.client.get(self.page).content.decode()
        # The answer also carries the message the redirect would have shown once.
        self.assertIn("Buy-in reversed.", answered)
        self.assertNotIn("Buy-in reversed.", fetched)
        without = re.sub(r'\s*<ul class="messages" role="status">.*?</ul>', "", clean(answered), flags=re.S)
        self.assertEqual(without, re.sub(r'\s*<ul class="messages" role="status">.*?</ul>', "", clean(fetched), flags=re.S))

    def test_without_the_header_the_redirect_is_unchanged(self):
        answer = self.buy(page=False)
        self.assertRedirects(answer, self.page, fetch_redirect_response=False)
        self.assertNotIn("X-In-Place-Location", answer)
        self.assertEqual(BuyIn.objects.count(), 1)

    def test_a_form_sent_from_another_page_gets_the_redirect(self):
        for page in ("/", reverse("night", args=[self.night.session.night_id]), "https://elsewhere.example" + self.page, "not a path"):
            answer = self.buy(page=page)
            self.assertEqual(answer.status_code, 302, page)

    def test_a_refusal_is_shown_on_the_page_and_nothing_is_written(self):
        answer = self.buy(amount="1")  # under the minimum buy-in
        self.assertEqual(answer.status_code, 200)
        self.assertContains(answer, "message-error")
        self.assertEqual(BuyIn.objects.count(), 0)

    def test_a_repeated_submission_writes_once(self):
        request_id = uuid.uuid4()
        for _ in range(2):
            self.assertEqual(self.buy(request_id=request_id).status_code, 200)
        self.assertEqual(BuyIn.objects.count(), 1)

    def test_the_answer_carries_a_token_and_a_request_id_that_work(self):
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.night.host.user)
        first = strict.get(self.page)
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', first.content.decode()).group(1)
        answer = self.buy(client=strict, csrfmiddlewaretoken=token)
        self.assertEqual(answer.status_code, 200)
        html = answer.content.decode()
        token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
        request_id = re.search(r'name="request_id" value="([^"]+)"', html).group(1)
        again = self.buy(client=strict, csrfmiddlewaretoken=token, request_id=request_id)
        self.assertEqual(again.status_code, 200)
        self.assertEqual(BuyIn.objects.count(), 2)

    def test_a_failure_while_drawing_the_page_falls_back_to_the_redirect(self):
        quiet = Client(raise_request_exception=False)  # the test client would raise what Django answers with a 500
        quiet.force_login(self.night.host.user)
        with mock.patch("web.views.session_context", side_effect=RuntimeError("boom")), \
                self.assertLogs("pokernights", "WARNING"), self.assertLogs("django.request", "ERROR"):
            answer = self.buy(client=quiet)
        self.assertRedirects(answer, self.page, fetch_redirect_response=False)
        self.assertEqual(BuyIn.objects.count(), 1)  # the write stands; the browser fetches the page itself
        self.assertContains(quiet.get(self.page), "₱1,000")

    @override_settings(ANSWER_IN_PLACE=False)
    def test_switched_off_every_answer_is_the_redirect(self):
        self.assertEqual(self.buy().status_code, 302)
        self.assertNotContains(self.client.get(self.page), "data-in-place")

    def test_pages_say_when_it_is_on(self):
        self.assertContains(self.client.get(self.page), 'data-in-place="on"')

    def test_a_page_view_is_never_touched(self):
        answer = self.client.get(self.page, HTTP_X_ANSWER_IN_PLACE=self.page)
        self.assertEqual(answer.status_code, 200)
        self.assertNotIn("X-In-Place-Location", answer)

    def test_someone_logged_out_is_sent_to_log_in(self):
        self.client.logout()
        answer = self.buy()
        self.assertEqual(answer.status_code, 302)
        self.assertIn(reverse("login"), answer["Location"])

    def test_one_request_costs_fewer_queries_than_two(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as two:
            self.buy(page=False)
            self.client.get(self.page)
        with CaptureQueriesContext(connection) as one:
            self.buy()
        self.assertLess(len(one), len(two))


class OneTripSessionPageTests(TestCase):
    def test_marking_a_transfer_paid(self):
        night = closed_example()
        self.client.force_login(night.host.user)
        page = reverse("night", args=[night.session.night_id])
        transfer = Transfer.objects.filter(plan__night_id=night.session.night_id).first()
        answer = self.client.post(
            reverse("transfer_paid", args=[night.session.night_id, transfer.pk]), {"request_id": uuid.uuid4()},
            HTTP_X_ANSWER_IN_PLACE=page,
        )
        self.assertEqual(answer.status_code, 200)
        self.assertEqual(answer["X-In-Place-Location"], page)
        self.assertEqual(Payment.objects.filter(transfer=transfer, active=True).count(), 1)
        self.assertContains(answer, "Undo")
