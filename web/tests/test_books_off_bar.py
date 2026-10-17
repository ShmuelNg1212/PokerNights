"""The host bar when every player is cashed out and the books differ: one coral line, and a button that leads somewhere."""
import re
import uuid

from django.test import TestCase
from django.urls import reverse

from ledger import services
from ledger.tests.test_counts import counting


class BooksOffBarTests(TestCase):
    def setUp(self):
        self.night = counting("A", "B")
        self.url = reverse("session", args=[self.night.session.pk])
        self.client.force_login(self.night.host.user)

    def bar(self):
        html = self.client.get(self.url).content.decode()
        start = html.index('class="dock-toggle')
        return html, html[start:html.index("</button>", start)]

    def off(self, b=1000):
        self.night.cash("A", 900)
        self.night.cash("B", b)

    def test_the_bar_says_missing_once_in_down_without_a_mark(self):
        self.off()
        _, bar = self.bar()
        self.assertIn('<span class="dock-gap" data-dock-gap>₱100 missing</span>', bar)
        self.assertNotIn("still to count", bar)
        self.assertNotIn("data-tone", bar)  # no warn mark, no brass
        # counts.js rewrites the bar only through these; without them it leaves the line alone.
        self.assertNotIn("data-dock-status", bar)
        self.assertNotIn("data-dock-coverage", bar)

    def test_extra_money_says_extra(self):
        self.off(b=1200)
        _, bar = self.bar()
        self.assertIn(">₱100 extra</span>", bar)

    def test_the_button_names_the_difference_and_falls_back_to_the_books(self):
        self.off()
        html, _ = self.bar()
        link = re.search(r'<a [^>]*data-books-gap[^>]*>([^<]*)</a>', html)
        self.assertIsNotNone(link)
        self.assertEqual(link.group(1), "See the ₱100 difference")
        self.assertIn('href="#balance"', link.group(0))
        self.assertIn('id="balance"', html)  # the anchor has somewhere to go without JavaScript
        self.assertIn('data-turbo="false"', link.group(0))

    def test_while_counting_the_bar_keeps_the_running_verdict(self):
        _, bar = self.bar()
        self.assertIn("data-dock-status", bar)
        self.assertIn("2 still to count.", bar)
        self.assertNotIn("data-dock-gap", bar)

    def test_an_override_keeps_its_covered_verdict(self):
        self.off()
        services.record_override(self.night.session.pk, self.night.host, "Synthetic recount", "player", self.night.players["A"].pk, uuid.uuid4())
        html, bar = self.bar()
        self.assertIn("Off by ₱100, covered by an override.", bar)
        self.assertNotIn("data-dock-gap", bar)
        self.assertNotIn("data-books-gap", html)

    def test_the_page_loads_the_script_that_answers_the_tap(self):
        self.off()
        html, _ = self.bar()
        self.assertIn("/static/js/gap.js", html)
