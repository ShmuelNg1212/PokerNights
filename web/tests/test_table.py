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

    def test_host_dock_toggle_names_the_next_step_in_each_state(self):
        for state, text in [('open', 'Next: Start the set'), ('running', 'Next: End play and count up')]:
            night = Night('Ben', state=state)
            self.client.force_login(night.host.user)
            page = self.client.get(reverse('session', args=[night.session.pk]))
            self.assertContains(page, 'class="dock-toggle"', count=1)
            self.assertContains(page, 'class="dock-toggle" hidden aria-expanded="true" data-focus-key="dock-toggle"')
            self.assertContains(page, text, count=1)
            self.assertContains(page, 'js/dock.js')

    def test_more_host_controls_options_are_buttons(self):
        page = self.client.get(self.url)
        self.assertContains(page, '<summary class="btn btn-quiet btn-block">Cancel this set</summary>')
        self.assertContains(page, '<summary class="btn btn-quiet btn-block">Or add one player</summary>')

    def test_host_dock_toggle_on_a_draft(self):
        from games import services as games
        night = Night(state='open')
        games.transition(night.session.pk, night.host, 'close')
        self.client.force_login(night.host.user)
        page = self.client.get(reverse('session', args=[night.session.pk]))
        self.assertContains(page, 'Next: Open for players', count=1)

    def test_host_dock_toggle_carries_the_count_verdict(self):
        self.night.go('reconciliation')
        page = self.client.get(self.url)
        self.assertContains(page, 'class="dock-toggle dock-total"', count=1)
        self.assertContains(page, 'data-dock-status data-tone="">₱1,000 still to account for.</span>')
        self.assertContains(page, 'data-dock-coverage>1 still to count.</span>')
        self.assertContains(page, 'class="dock-count"', count=1)
        self.assertRegex(page.content.decode(), r'<span data-dock-prefix></span><strong data-dock-accounted>₱[\d,]+</strong> of ₱[\d,]+ bought in')
        self.assertNotContains(page, 'Next:')

    def test_player_and_final_set_have_no_dock_toggle(self):
        member = self.night.add_login_player('viewer')
        self.client.force_login(member.user)
        self.assertNotContains(self.client.get(self.url), 'dock-toggle')

    def test_count_up_keeps_the_one_form_and_has_no_results(self):
        self.night.go('reconciliation')
        page = self.client.get(self.url)
        self.assertContains(page, 'id="counts-form"', count=1)
        self.assertContains(page, 'form="counts-form"')
        self.assertContains(page, 'Confirm all counts')
        self.assertNotContains(page, 'Results of set')


class RowActionTests(TestCase):
    """Buy-in, Rebuy and Cash out are written on the row; none is hidden behind an icon or the details sheet."""

    def setUp(self):
        from groups.tests.helpers import make_group, add_player
        from games.tests.helpers import make_session
        import uuid
        from games import services as games
        from ledger import services as ledger
        self.group, self.host = make_group()
        self.player = add_player(self.group, "viewer")
        self.session = make_session(self.host, state="open")
        first, second = games.add_participants(self.session.pk, self.host, [self.host.pk, self.player.pk], uuid.uuid4())
        self.first, self.second = first, second
        ledger.record_buy_in(self.session.pk, self.host, first.pk, 100000, uuid.uuid4())
        self.url = reverse("session", args=[self.session.pk])
        self.client.force_login(self.host.user)

    def test_open_set_labels_rebuy_and_buy_in_and_offers_no_cash_out(self):
        page = self.client.get(self.url).content.decode()
        self.assertIn(f'data-sheet-open="buy-{self.first.pk}" aria-label="Rebuy for', page)
        self.assertIn(f'data-sheet-open="buy-{self.second.pk}" aria-label="Buy-in for', page)
        self.assertNotIn("cash-opener", page)

    def test_running_set_offers_cash_out_only_to_players_with_money(self):
        from games import services as games
        games.transition(self.session.pk, self.host, "start", opening_buy_ins=False)
        page = self.client.get(self.url).content.decode()
        self.assertIn(f'data-sheet-open="cash-{self.first.pk}"', page)
        self.assertIn(f'data-sheet-source="cash-{self.first.pk}"', page)
        self.assertNotIn(f'data-sheet-open="cash-{self.second.pk}"', page)
        # One cash-out form per player: the details sheet no longer repeats it.
        self.assertEqual(page.count(f'name="participant_id" value="{self.first.pk}"'), 2)

    def test_player_sees_no_money_actions(self):
        from games import services as games
        games.transition(self.session.pk, self.host, "start", opening_buy_ins=False)
        self.client.force_login(self.player.user)
        page = self.client.get(self.url).content.decode()
        self.assertNotIn("player-actions", page)
        self.assertNotIn("cash-opener", page)


class SetPageRevampTests(TestCase):
    """The set page in play since 2026-10-09: a short panel, one-line rows, Cash out in the player's sheet."""

    def setUp(self):
        import uuid
        from games import services as games
        from games.tests.helpers import make_session
        from groups.tests.helpers import add_player, make_group
        from ledger import services as ledger
        self.group, self.host = make_group()
        self.ana, self.ben = add_player(self.group, "ana"), add_player(self.group, "ben")
        self.session = make_session(self.host, state="open")
        self.seats = games.add_participants(self.session.pk, self.host, [self.ana.pk, self.ben.pk], uuid.uuid4())
        for seat in self.seats:
            ledger.record_buy_in(self.session.pk, self.host, seat.pk, 100000, uuid.uuid4())
        games.transition(self.session.pk, self.host, "start", opening_buy_ins=False)
        self.url = reverse("session", args=[self.session.pk])
        self.client.force_login(self.host.user)

    def page(self):
        return self.client.get(self.url).content.decode()

    def test_the_panel_keeps_the_figure_and_puts_the_facts_behind_one_line(self):
        page = self.page()
        self.assertIn('class="table-layout table-v2"', page)
        self.assertIn('<span class="badge badge-live">In play</span>', page)
        self.assertIn('data-watch="in-play" data-value="200000"', page)
        self.assertIn('<details class="set-facts" data-key="set-facts" data-wide-open>', page)
        self.assertIn("<strong>₱2,000</strong> bought in · <strong>₱0</strong> cashed out", page)
        facts = page[page.index('class="facts-body"'):page.index("</details>", page.index('class="facts-body"'))]
        self.assertIn("Total bought in", facts)
        self.assertIn("(2 buy-ins)", facts)
        self.assertIn("Rake is Off.", facts)
        # Rake rows belong to a set that takes rake.
        self.assertNotIn("Collected rake", page)

    def test_rake_rows_show_when_the_set_takes_rake(self):
        from games import services as games
        current = games.current_settings(self.session)
        # Written straight to the row: the service refuses a new rule once money is in.
        type(current).objects.filter(pk=current.pk).update(rake_mode="flat", rake_flat=5000)
        page = self.page()
        self.assertIn("Collected rake", page)
        self.assertIn("Available to play", page)

    def test_a_row_is_watched_as_before_and_opens_the_players_sheet(self):
        page = self.page()
        seat = self.seats[0]
        self.assertIn(f'data-watch="player-{seat.pk}" data-value="100000:1:0:joined"', page)
        self.assertIn(f'class="player-name player-opener" data-sheet-open="player-{seat.pk}"', page)
        self.assertIn(f'data-sheet-open="buy-{seat.pk}" aria-label="Rebuy for', page)
        sheet = page[page.index(f'data-sheet-source="player-{seat.pk}"'):]
        sheet = sheet[:sheet.index("</details>")]
        # The sheet leads with Cash out, then says what was bought in, then the records.
        self.assertLess(sheet.index(f'data-sheet-swap="cash-{seat.pk}"'), sheet.index("Bought in <strong>₱1,000</strong>"))
        self.assertLess(sheet.index("Bought in <strong>₱1,000</strong>"), sheet.index("Buy-in ·"))
        # Without the sheet, Cash out is still its own native disclosure with one form.
        self.assertIn(f'data-sheet-source="cash-{seat.pk}"', page)

    def test_a_player_without_money_has_no_cash_out_in_the_sheet(self):
        import uuid
        from games import services as games
        from groups.tests.helpers import add_player
        late = add_player(self.group, "cho")
        seat = games.add_participants(self.session.pk, self.host, [late.pk], uuid.uuid4())[0]
        self.assertNotIn(f'data-sheet-swap="cash-{seat.pk}"', self.page())

    def test_the_host_sees_join_under_the_list_and_keeps_the_order_of_joining(self):
        page = self.page()
        self.assertIn('class="join-row join-row-quiet"', page)
        self.assertLess(page.index(f'data-watch="player-{self.seats[0].pk}"'), page.index(f'data-watch="player-{self.seats[1].pk}"'))
        self.assertLess(page.index(f'data-watch="player-{self.seats[1].pk}"'), page.index("join-row-quiet"))

    def test_a_player_sees_their_own_row_first_and_once(self):
        self.client.force_login(self.ben.user)
        page = self.page()
        own, other = f'data-watch="player-{self.seats[1].pk}"', f'data-watch="player-{self.seats[0].pk}"'
        self.assertLess(page.index(own), page.index(other))
        self.assertEqual(page.count(own), 1)
        self.assertNotIn("join-row", page)

    def test_the_polling_answer_is_the_same_page(self):
        import json
        answer = json.loads(self.client.get(reverse("session_state", args=[self.session.pk])).content)
        self.assertIn('class="table-layout table-v2"', answer["html"])
        self.assertIn("data-sheet-swap", answer["html"])

    def test_the_switch_returns_the_page_as_it_was(self):
        from django.test import override_settings
        with override_settings(TABLE_REVAMP=False):
            page = self.page()
        self.assertNotIn("table-v2", page)
        self.assertNotIn("set-facts", page)
        self.assertNotIn("data-sheet-swap", page)
        self.assertIn('<span class="badge badge-live">Running</span>', page)
        self.assertIn("Collected rake", page)
        self.assertIn('class="join-row"', page)

    def test_no_query_is_added_for_the_new_page(self):
        from django.db import connection
        from django.test import override_settings
        from django.test.utils import CaptureQueriesContext
        with CaptureQueriesContext(connection) as new:
            self.client.get(self.url)
        with override_settings(TABLE_REVAMP=False), CaptureQueriesContext(connection) as old:
            self.client.get(self.url)
        self.assertEqual(len(new), len(old))
