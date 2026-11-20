"""Cash out and Reverse apart (doc/plan/1795144795_cash_out_and_reverse.md).

A red Reverse button and its reason field show only inside a closed "Reverse…" disclosure, under the records' hairline.
"""

import re

from django.test import TestCase
from django.urls import reverse

from ledger.models import BuyInReversal
from ledger.tests.helpers import Night


def reverse_blocks(html):
    return re.findall(r'<details class="reverse-entry"[^>]*>.*?</details>', html, flags=re.S)


class ReverseApartTests(TestCase):
    def setUp(self):
        self.night = Night("A", "B")
        self.bought = self.night.buy("A", 1000)
        self.night.buy("B", 500)
        self.night.cash("B", 200)
        self.page = reverse("session", args=[self.night.session.pk])
        self.client.force_login(self.night.host.user)

    def html(self):
        return self.client.get(self.page).content.decode()

    def test_every_reverse_button_is_inside_a_closed_disclosure(self):
        html = self.html()
        blocks = reverse_blocks(html)
        self.assertTrue(blocks)
        for block in blocks:
            self.assertNotRegex(block.split(">", 1)[0], r"\bopen\b")
            self.assertIn('<summary class="btn btn-small btn-quiet">Reverse…</summary>', block)
        outside = html
        for block in blocks:
            outside = outside.replace(block, "")
        self.assertNotIn("Reason for reversal", outside)
        self.assertNotRegex(outside, r'btn-danger">Reverse')

    def test_the_red_button_names_the_amount(self):
        self.assertIn('<button type="submit" class="btn btn-danger">Reverse ₱1,000</button>', self.html())

    def test_the_records_sit_under_a_heading_for_the_host(self):
        html = self.html()
        self.assertIn('<div class="records">', html)
        self.assertIn("Records and corrections", html)

    def test_a_player_sees_records_without_corrections(self):
        member = self.night.add_login_player("C")
        self.night.buy("C", 1000)
        self.client.force_login(member.user)
        html = self.html()
        self.assertNotIn("Reverse…", html)
        self.assertNotIn("Records and corrections", html)

    def test_the_form_still_reverses_with_its_reason(self):
        self.client.post(
            reverse("buy_in_reverse", args=[self.night.session.pk, self.bought.pk]), {"reason": "typed twice"},
        )
        self.assertEqual(BuyInReversal.objects.get(buy_in=self.bought).reason, "typed twice")
