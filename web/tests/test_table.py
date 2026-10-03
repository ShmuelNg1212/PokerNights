"""Presentation and fallback behavior; accounting is tested in the existing suite."""
from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from ledger.tests.helpers import Night
from web.templatetags.table_tags import player_token, buy_in_stack


class TokenTests(SimpleTestCase):
    def player(self, name, order):
        return SimpleNamespace(member=SimpleNamespace(display_name=name), join_order=order)

    def test_shared_initial_uses_two_letters(self):
        ben, bea = self.player('Ben', 1), self.player('Bea Santos', 2)
        self.assertIn('>BE<', player_token(ben, [ben, bea]))
        self.assertIn('>BS<', player_token(bea, [ben, bea]))

    def test_palette_repeats_after_ten_and_names_are_escaped(self):
        player = self.player('<B>', 11)
        token = player_token(player, [player])
        self.assertIn('k1', token)
        self.assertIn('&lt;', token)
        self.assertNotIn('<B>', token)

    def test_bea_and_ben_have_distinct_tokens(self):
        bea, ben = self.player('Bea', 6), self.player('Ben', 8)
        self.assertIn('>BE<', player_token(bea, [bea, ben]))
        self.assertIn('>BN<', player_token(ben, [bea, ben]))

    def test_stack_caps_at_five_and_states_overflow(self):
        self.assertEqual(buy_in_stack(8).count('<i>'), 5)
        self.assertIn('+3', buy_in_stack(8))


class TablePageTests(TestCase):
    def setUp(self):
        self.night = Night('Ben', 'Bea')
        self.night.buy('Ben', 1000)
        self.client.force_login(self.night.host.user)
        self.url = reverse('session', args=[self.night.session.pk])

    def test_active_rows_have_real_native_form_fallbacks(self):
        page = self.client.get(self.url)
        self.assertContains(page, 'data-sheet-source="buy-')
        self.assertContains(page, 'data-sheet-source="player-')
        self.assertContains(page, 'name="request_id"')
        self.assertContains(page, reverse('buy_in_add', args=[self.night.session.pk]))
        self.assertContains(page, reverse('cash_out_add', args=[self.night.session.pk]))
        self.assertContains(page, 'Allowed: ₱500–₱2,000')
        self.assertContains(page, 'data-watch="in-play"')
        self.assertContains(page, 'Total bought in')
        self.assertContains(page, 'Still in play')

    def test_player_page_has_no_host_sheet_or_correction(self):
        member = self.night.add_login_player('viewer')
        self.client.force_login(member.user)
        page = self.client.get(self.url)
        self.assertNotContains(page, 'buy-opener')
        self.assertNotContains(page, 'buyins/add')
        self.assertNotContains(page, 'next-action')

    def test_count_up_keeps_the_one_form_and_has_no_results(self):
        self.night.go('reconciliation')
        page = self.client.get(self.url)
        self.assertContains(page, 'id="counts-form"', count=1)
        self.assertContains(page, 'form="counts-form"')
        self.assertContains(page, 'Confirm all counts')
        self.assertNotContains(page, 'Results of set')
