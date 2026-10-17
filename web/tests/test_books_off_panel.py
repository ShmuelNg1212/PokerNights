"""The books-off panel: the gap in words, one sentence, causes behind a disclosure, and an override that is not success."""
import re
import uuid

from django.test import TestCase
from django.urls import reverse

from ledger import queries, services
from ledger.tests.helpers import Night
from ledger.tests.test_rake import configure


def off_by_100(rake=False):
    """A host, Miguel and Carlo (a login player): everyone cashed out, ₱100 short."""
    night = Night("Miguel")
    if rake:
        configure(night, rake_mode="flat", rake_flat=5000, rake_basis_points=0)
    carlo = night.add_login_player("Carlo")
    night.buy("Miguel", 1000)
    night.buy("Carlo", 1000)
    night.go("reconciliation")
    rake_each = 50 if rake else 0
    night.cash("Miguel", 1000 - rake_each)
    night.cash("Carlo", 900 - rake_each)
    return night, carlo


class BooksOffPanelTests(TestCase):
    def setUp(self):
        self.night, self.carlo = off_by_100()
        self.url = reverse("session", args=[self.night.session.pk])

    def page(self, user):
        self.client.force_login(user)
        return self.client.get(self.url).content.decode()

    def panel(self, html):
        start = html.index('<div class="discrepancy"')
        return html[start:html.index('<dl class="set-totals', start)]

    def test_the_gap_leads_in_words_with_a_stable_hook(self):
        html = self.page(self.night.host.user)
        panel = self.panel(html)
        self.assertIn('id="books-gap"', panel)
        self.assertIn('data-gap="-10000"', panel)
        self.assertIn('<p class="discrepancy-amount">₱100 missing</p>', panel)
        self.assertNotIn("−₱100", panel)
        self.assertNotIn("off by", panel.lower())
        self.assertIn("Cash-outs are ₱100 below buy-ins.", panel)
        self.assertNotIn("rake", panel)

    def test_the_alert_is_the_short_statement_and_the_causes_wait_closed(self):
        panel = self.panel(self.page(self.night.host.user))
        alert = re.search(r'<div class="discrepancy-statement" role="alert">(.*?)</div>', panel, re.S).group(1)
        self.assertIn("₱100 missing", alert)
        self.assertNotIn("Look for", alert)
        self.assertEqual(panel.count('role="alert"'), 1)
        where = panel[panel.index("<details"):]
        self.assertIn("<summary>Where to look</summary>", where)
        self.assertNotIn("<details open", panel)
        self.assertIn("A buy-in recorded twice", where)
        self.assertIn("record an override below", where)

    def test_too_much_reads_above(self):
        services.reverse_cash_out(self.night.session.pk, self.night.host,
                                  self.night.line("Carlo").cash_outs[0].pk, "recount")
        self.night.cash("Carlo", 1200)
        panel = self.panel(self.page(self.night.host.user))
        self.assertIn('<p class="discrepancy-amount">₱200 too much</p>', panel)
        self.assertIn("Cash-outs are ₱200 above buy-ins.", panel)
        self.assertIn("A cash-out that is too high", panel)

    def test_a_player_sees_no_host_instructions_and_their_own_figures(self):
        html = self.page(self.carlo.user)
        panel = self.panel(html)
        self.assertIn("₱100 missing", panel)
        self.assertIn("The host is checking the records. Results are final once the books balance.", panel)
        self.assertIn("You: ₱1,000 in · ₱900 out", panel)
        self.assertNotIn("Where to look", panel)
        self.assertNotIn("Reverse and re-enter", html)
        self.assertNotIn("Finalize with an override", html)

    def test_one_statement_once_everyone_is_cashed_out(self):
        html = self.page(self.carlo.user)
        self.assertNotIn("Confirmed counts", html)
        self.assertNotIn("data-count-coverage", html)

    def test_the_override_link_stays_in_place(self):
        html = self.page(self.night.host.user)
        self.assertIn('<details data-key="override">', html)
        self.assertIn("Cannot find the error? Finalize with an override", html)


class RakeWordingTests(TestCase):
    def test_rake_is_named_only_when_collected(self):
        night, _ = off_by_100(rake=True)
        balance = queries.balance(night.session)
        self.assertEqual(balance.headline, "₱100 missing")
        self.assertEqual(balance.gap_sentence, "Cash-outs plus rake are ₱100 below buy-ins.")
        self.assertIn("cash-outs plus rake are below", balance.explanation)

    def test_without_rake_only_cash_outs_are_compared(self):
        night, _ = off_by_100()
        balance = queries.balance(night.session)
        self.assertEqual(balance.gap_sentence, "Cash-outs are ₱100 below buy-ins.")
        self.assertIn("cash-outs are below", balance.explanation)
        self.assertNotIn("rake", balance.explanation)


class OverrideIsNotSuccessTests(TestCase):
    def setUp(self):
        self.night, self.carlo = off_by_100()
        services.record_override(self.night.session.pk, self.night.host, "Synthetic recount",
                                 "player", self.night.players["Miguel"].pk, uuid.uuid4())
        self.url = reverse("session", args=[self.night.session.pk])

    def test_covered_reads_neutral_names_the_absorber_and_never_draws_balanced(self):
        self.client.force_login(self.night.host.user)
        html = self.client.get(self.url).content.decode()
        self.assertIn('<div class="books-covered">', html)
        self.assertIn("Off by ₱100, covered by an override from Miguel.", html)
        self.assertNotIn("data-balance=", html)
        self.assertNotIn("books-balanced", html)
        self.assertNotIn('id="books-gap"', html)

    def test_equal_shares_name_everyone_plainly(self):
        services.void_override(self.night.session.pk, self.night.host)
        services.record_override(self.night.session.pk, self.night.host, "Split", "equal", None, uuid.uuid4())
        self.assertEqual(queries.balance(self.night.session).covered_text,
                         "Off by ₱100, covered by an override from Miguel and Carlo.")

    def test_true_balance_keeps_the_once_only_moment(self):
        services.void_override(self.night.session.pk, self.night.host)
        services.reverse_cash_out(self.night.session.pk, self.night.host,
                                  self.night.line("Carlo").cash_outs[0].pk, "recount")
        self.night.cash("Carlo", 1000)
        self.client.force_login(self.night.host.user)
        html = self.client.get(self.url).content.decode()
        self.assertIn(f'data-balance="{self.night.session.pk}"', html)
        self.assertNotIn("books-covered", html)


class CoverageTextTests(TestCase):
    def test_nothing_left_to_count_says_nothing(self):
        night, _ = off_by_100()
        self.assertEqual(queries.count_total(night.session).coverage_text, "")

    def test_players_still_to_count_are_counted(self):
        night = Night("A", "B")
        night.buy("A", 1000)
        night.buy("B", 1000)
        night.go("reconciliation")
        self.assertEqual(queries.count_total(night.session).coverage_text, "2 still to count.")
