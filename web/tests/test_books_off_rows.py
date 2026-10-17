"""Books off with everyone cashed out: each row shows its in, out and net, and marks a cash-out that differs from its count."""
import re
import uuid
from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from ledger import money, queries, services
from ledger.models import FinalCount
from ledger.tests.helpers import Night
from ledger.tests.test_counts import count


def batch(night):
    ids = FinalCount.objects.filter(session=night.session, is_current=True).values_list("pk", flat=True)
    services.cash_out_counted(night.session.pk, night.host, list(ids), uuid.uuid4())


def clear(night, name):
    services.clear_count(night.session.pk, night.host, night.players[name].pk)


class BooksOffRowsTests(TestCase):
    def setUp(self):
        self.night = Night("Miguel", "Carlo")
        self.ben = self.night.add_login_player("Ben")
        for name in self.night.players:
            self.night.buy(name, 1000)
        self.night.go("reconciliation")
        self.url = reverse("session", args=[self.night.session.pk])

    def page(self, user=None):
        self.client.force_login(user or self.night.host.user)
        return self.client.get(self.url).content.decode()

    def row(self, html, name):
        pk = self.night.players[name].pk
        start = html.index(f'id="count-row-{pk}"')
        start = html.rindex("<li", 0, start)
        return html[start:html.index("</li>", start)]

    def signed(self, pesos):
        return money.format_signed_amount(pesos * 100, "php")

    def test_each_cashed_out_row_shows_in_out_and_a_signed_net(self):
        count(self.night, "Miguel", 1000)
        count(self.night, "Carlo", 900)
        count(self.night, "Ben", 1250)
        batch(self.night)
        html = self.page()
        carlo = self.row(html, "Carlo")
        self.assertIn("<span>₱1,000 in</span> · <span>₱900 out</span>", carlo)
        self.assertIn('class="count-net minus"', carlo)
        self.assertIn("icon-arrow-down-right", carlo)  # colour is never the only signal
        self.assertIn(self.signed(-100), carlo)
        ben = self.row(html, "Ben")
        self.assertIn('class="count-net plus"', ben)
        self.assertIn("icon-arrow-up-right", ben)
        self.assertIn(self.signed(250), ben)
        miguel = self.row(html, "Miguel")
        self.assertIn('class="count-net "', miguel)
        self.assertIn("icon-minus", miguel)
        self.assertIn("Even", miguel)
        # The cash-out itself carries no win or loss class: its colour is Bone in the books-off block.
        outcome = carlo[carlo.index('class="count-outcome"'):]
        self.assertNotIn("plus", outcome)
        self.assertNotIn("minus", outcome)
        # A batch cash-out is the count itself, so nothing is suspect.
        self.assertNotIn("data-suspect", html)
        self.assertNotIn("count-gap", html)

    def test_a_player_sees_the_same_rows(self):
        count(self.night, "Miguel", 1000)
        count(self.night, "Carlo", 900)
        count(self.night, "Ben", 1000)
        batch(self.night)
        html = self.page(self.ben.user)
        self.assertIn("<span>₱1,000 in</span> · <span>₱900 out</span>", self.row(html, "Carlo"))
        self.assertIn(self.signed(-100), self.row(html, "Carlo"))

    def test_a_hand_typed_cash_out_that_differs_from_its_count_is_marked(self):
        for name in ("Miguel", "Carlo", "Ben"):
            count(self.night, name, 1000)
        self.night.cash("Carlo", 900)  # typed by hand over the confirmed ₱1,000
        batch(self.night)
        html = self.page()
        carlo = self.row(html, "Carlo")
        self.assertIn("data-suspect", carlo)
        self.assertIn('data-suspect="full"', carlo)
        self.assertIn('<span class="count-gap"><span>Counted ₱1,000</span> · <span>cashed out ₱900</span> · <span>explains the gap</span></span>', carlo)
        self.assertNotIn("data-suspect", self.row(html, "Miguel"))
        self.assertEqual(html.count("data-suspect"), 1)
        # The order of the rows does not change.
        ids = re.findall(r'id="count-row-(\d+)"', html)
        self.assertEqual([int(i) for i in ids], [self.night.players[n].pk for n in ("Miguel", "Carlo", "Ben")])
        self.assertEqual(html.count("data-suspect"), 1, "a player's page marks it too")

    def test_a_hand_typed_cash_out_equal_to_its_count_is_not_marked(self):
        for name in ("Miguel", "Ben"):
            count(self.night, name, 1000)
        count(self.night, "Carlo", 900)
        self.night.cash("Miguel", 1000)
        batch(self.night)
        html = self.page()
        self.assertIn("<span>₱1,000 in</span> · <span>₱900 out</span>", self.row(html, "Carlo"))
        self.assertNotIn("data-suspect", html)

    def test_a_count_cleared_before_the_cash_out_is_not_compared(self):
        for name in ("Miguel", "Carlo", "Ben"):
            count(self.night, name, 1000)
        clear(self.night, "Carlo")
        self.night.cash("Carlo", 900)
        batch(self.night)
        self.assertEqual(queries.count_gaps(queries.summary(self.night.session)), {})
        self.assertNotIn("data-suspect", self.page())

    def test_a_partial_cash_out_during_play_is_not_a_gap(self):
        night = Night("A", "B")
        for name in night.players:
            night.buy(name, 1000)
        night.cash("A", 100)  # partial, while playing
        night.go("reconciliation")
        count(night, "A", 900)
        count(night, "B", 800)
        batch(night)
        self.assertEqual(queries.count_gaps(queries.summary(night.session)), {})

    def test_count_gaps_names_the_counted_and_cashed_amounts(self):
        for name in ("Miguel", "Carlo", "Ben"):
            count(self.night, name, 1000)
        self.night.cash("Ben", 700)
        batch(self.night)
        gaps = queries.count_gaps(queries.summary(self.night.session))
        self.assertEqual(gaps, {self.night.players["Ben"].pk: (100000, 70000)})

    def test_nothing_shows_when_the_books_balance(self):
        for name in ("Miguel", "Carlo", "Ben"):
            count(self.night, name, 1000)
        batch(self.night)
        html = self.page()
        self.assertNotIn("count-books", html)
        self.assertNotIn("data-suspect", html)
        self.assertIn('id="count-row-', html)  # the ids are there in every state

    def test_nothing_shows_while_a_player_is_still_to_cash_out(self):
        count(self.night, "Miguel", 1000)
        count(self.night, "Carlo", 900)
        self.night.cash("Carlo", 800)
        services.cash_out_counted(
            self.night.session.pk, self.night.host,
            [FinalCount.objects.get(participant=self.night.players["Miguel"], is_current=True).pk], uuid.uuid4(),
        )
        html = self.page()
        self.assertNotIn("count-books", html)
        self.assertNotIn("data-suspect", html)

    def test_the_cash_out_amount_is_bone_during_count_up(self):
        css = Path(settings.BASE_DIR, "static/css/app.css").read_text()
        block = css[css.index("/* Books off: the rows (2026-10-17) */"):]
        self.assertIn(".count-row.is-cashed_out .count-outcome .num { color: var(--bone); }", block)

    def test_only_a_record_that_moves_the_books_the_way_they_are_off_is_marked(self):
        # Carlo typed ₱100 under his count, Ben ₱150 over his: the books are ₱50 too much, so only Ben can explain it, in part.
        for name in ("Miguel", "Carlo", "Ben"):
            count(self.night, name, 1000)
        self.night.cash("Carlo", 900)
        self.night.cash("Ben", 1150)
        batch(self.night)
        html = self.page()
        self.assertNotIn("data-suspect", self.row(html, "Carlo"))
        ben = self.row(html, "Ben")
        self.assertIn('data-suspect="part"', ben)
        self.assertIn("<span>₱150 more than counted</span>", ben)
        self.assertEqual(html.count("data-suspect"), 1)
