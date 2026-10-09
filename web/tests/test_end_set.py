"""Rack end-of-set presentation; services retain their existing accounting tests."""
import copy
import uuid
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from ledger import queries, services
from ledger.tests.helpers import Night
from settlement import services as settlement
from web.templatetags.table_tags import player_token


class EndSetPageTests(TestCase):
    def setUp(self):
        self.night = Night('Ben', 'Bea', 'Watcher')
        self.night.buy('Ben', 1000)
        self.night.buy('Bea', 1000)
        self.night.cash('Ben', 200)
        self.night.go('reconciliation')
        self.client.force_login(self.night.host.user)
        self.url = reverse('session', args=[self.night.session.pk])

    def count(self, name, amount):
        return services.confirm_count(self.night.session.pk, self.night.host,
                                      self.night.players[name].pk, amount * 100, uuid.uuid4())

    def test_progress_excludes_no_money_and_partial_cash_out(self):
        page = self.client.get(self.url)
        self.assertContains(page, '<strong>0 <span>of 2</span></strong>')
        self.assertContains(page, 'Recorded cash-outs</dt><dd>₱200')
        self.assertNotContains(page, 'data-balance=')
        self.count('Ben', 800)
        page = self.client.get(self.url)
        self.assertContains(page, '<strong>1 <span>of 2</span></strong>')
        self.assertContains(page, 'Counted ₱800')
        self.assertNotContains(page, 'Your result')

    def test_review_keeps_exact_count_ids_and_adds_to_earlier_cash_outs(self):
        count = self.count('Ben', 800)
        page = self.client.get(reverse('cash_out_counted', args=[self.night.session.pk]))
        self.assertContains(page, f'name="count_id" value="{count.pk}"')
        self.assertContains(page, 'After this batch</dt><dd>₱1,000')
        self.assertContains(page, 'Recorded cash-outs</dt><dd>₱200')
        self.assertContains(page, 'name="request_id"')
        self.assertContains(page, 'It does not finalize the set')

    def test_equal_recorded_totals_with_missing_final_cash_out_do_not_balance(self):
        self.night.cash('Bea', 1800)
        page = self.client.get(self.url)
        self.assertContains(page, 'Total cashed out</span><span class="amount">₱2,000')
        self.assertNotContains(page, 'data-balance=')
        self.assertNotContains(page, 'Finalize results')
        self.assertNotContains(page, 'role="alert"')

    def test_only_balanced_books_offer_one_native_finalize_form(self):
        self.night.cash('Ben', 800)
        self.night.cash('Bea', 1000)
        page = self.client.get(self.url)
        self.assertContains(page, f'data-balance="{self.night.session.pk}"', count=1)
        self.assertContains(page, reverse('session_finalize', args=[self.night.session.pk]), count=1)

    def test_completed_discrepancy_is_an_alert_and_override_stays_disclosed(self):
        self.night.cash('Ben', 700)
        self.night.cash('Bea', 1000)
        page = self.client.get(self.url)
        self.assertContains(page, 'role="alert"')
        self.assertContains(page, '₱100 is missing')
        self.assertNotContains(page, 'data-balance=')
        services.record_override(self.night.session.pk, self.night.host, 'Synthetic recount',
                                 'player', self.night.players['Ben'].pk, uuid.uuid4())
        page = self.client.get(self.url)
        self.assertContains(page, 'A host override covers the difference')
        self.assertContains(page, 'Synthetic recount')
        self.assertContains(page, 'Finalize results')

    def test_final_results_use_snapshot_even_if_summary_differs(self):
        self.night.cash('Ben', 800)
        self.night.cash('Bea', 1000)
        settlement.finalize(self.night.session.pk, self.night.host)
        summary = queries.summary(self.night.session)
        summary.lines[0].buy_ins = []  # Simulate a divergent read, without writing any record.
        with patch('web.views.ledger_queries.summary', return_value=summary):
            page = self.client.get(self.url)
        self.assertContains(page, 'Bought in (1)</dt><dd>₱1,000')
        self.assertContains(page, 'class="result-amount')
        self.assertContains(page, 'Results of set 1')
        self.assertNotContains(page, 'counts-form')
        self.assertNotContains(page, 'cashouts/add')
        self.assertNotContains(page, 'transfers/')

    def test_token_disambiguation_matches_query_instances_by_pk(self):
        ben, bea = self.night.players['Ben'], self.night.players['Bea']
        self.assertEqual(player_token(copy.copy(ben), [ben, bea]), player_token(ben, [ben, bea]))
        self.assertEqual(player_token(copy.copy(bea), [ben, bea]), player_token(bea, [ben, bea]))
        self.assertNotEqual(player_token(ben, [ben, bea]), player_token(bea, [ben, bea]))

    def test_empty_count_up_has_no_finalize_or_percentage(self):
        empty = Night('Watcher')
        empty.go('reconciliation')
        self.client.force_login(empty.host.user)
        page = self.client.get(reverse('session', args=[empty.session.pk]))
        # No progress figure without players to count: "0 of 0" would mean nothing.
        self.assertNotContains(page, '<span>of 0</span>')
        self.assertContains(page, 'nothing to count')
        self.assertContains(page, 'No buy-in is recorded')
        self.assertNotContains(page, 'Finalize results')
        self.assertNotContains(page, 'data-balance=')

    def test_chips_count_and_final_states_have_no_peso(self):
        night = Night('A', unit='chips')
        night.buy('A', 1000)
        night.go('reconciliation')
        self.client.force_login(night.host.user)
        url = reverse('session', args=[night.session.pk])
        page = self.client.get(url)
        self.assertNotContains(page, '₱')
        self.assertContains(page, 'Final count (chips)')
        night.cash('A', 1000)
        settlement.finalize(night.session.pk, night.host)
        page = self.client.get(url)
        self.assertNotContains(page, '₱')
        self.assertContains(page, '1,000 chips')


class NeutralStateTests(TestCase):
    """The blue felt belongs to a set in play; every other state has a neutral lead panel."""

    def test_only_a_running_set_uses_the_felt(self):
        night = Night('A', state='open')
        self.client.force_login(night.host.user)
        url = reverse('session', args=[night.session.pk])
        # An open set is being prepared: a checklist on the neutral surface, and no felt.
        page = self.client.get(url)
        self.assertContains(page, '<section class="prep" data-unit')
        self.assertNotContains(page, 'class="felt')
        night.go('running')
        page = self.client.get(url)
        self.assertContains(page, '<section class="felt" data-unit')
        self.assertNotContains(page, 'split-track')
        night.buy('A', 1000)
        night.go('reconciliation')
        self.assertContains(self.client.get(url), 'class="felt hero"')
        self.assertContains(self.client.get(reverse('night', args=[night.session.night_id])), 'class="felt hero"')

    def test_discrepancy_states_the_signed_amount_and_waiting_is_not_a_warning(self):
        night = Night('A', 'B')
        night.buy('A', 1000); night.buy('B', 1000)
        night.go('reconciliation')
        self.client.force_login(night.host.user)
        url = reverse('session', args=[night.session.pk])
        page = self.client.get(url)
        self.assertContains(page, 'class="notice notice-info"')
        self.assertNotContains(page, 'class="discrepancy"')
        night.cash('A', 1500); night.cash('B', 400)
        page = self.client.get(url)
        self.assertContains(page, '<p class="discrepancy-amount">−₱100</p>')
        self.assertContains(page, 'role="alert"')
