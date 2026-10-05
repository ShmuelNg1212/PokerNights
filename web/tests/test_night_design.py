"""Session presentation derives money from transfers and frozen results."""
import uuid
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from games import services as games
from games.models import GameNight
from ledger.tests.helpers import Night
from settlement import queries, services
from settlement.tests.test_night import TwoSets


class NightDesignTests(TestCase):
    def setUp(self):
        self.two = TwoSets()
        self.night = GameNight.objects.get(pk=self.two.night_id)
        self.client.force_login(self.two.host.user)
        self.url = reverse('night', args=[self.night.pk])

    def close(self):
        services.close_night(self.night.pk, self.two.host)
        self.night.refresh_from_db()

    def test_progress_tracks_unequal_amounts_and_undo_keeps_results(self):
        self.close()
        before = queries.night_outcome(self.night)
        transfer = before.transfers[0]
        request = uuid.uuid4()
        services.mark_paid(self.night.pk, self.two.host, transfer.pk, request)
        services.mark_paid(self.night.pk, self.two.host, transfer.pk, request)
        after = queries.night_outcome(self.night)
        self.assertEqual((after.total_to_pay, after.paid_amount, after.still_to_pay), (30000, 20000, 10000))
        self.assertEqual(after.paid_count, 1)
        self.assertEqual([s.net for s in before.standings], [s.net for s in after.standings])
        self.assertContains(self.client.get(self.url), 'value="20000" max="30000"')
        services.mark_unpaid(self.night.pk, self.two.host, transfer.pk)
        after = queries.night_outcome(self.night)
        self.assertEqual(after.still_to_pay, 30000)
        self.assertEqual([s.net for s in before.standings], [s.net for s in after.standings])
        self.assertContains(self.client.get(self.url), '· undone')

    def test_open_results_are_not_settled_and_recap_is_closed_only(self):
        page = self.client.get(self.url)
        self.assertContains(page, 'Over finalized sets; session still open.')
        self.assertNotContains(page, 'Still to pay')
        self.assertNotContains(page, 'data-recap=')
        self.close()
        page = self.client.get(self.url)
        self.assertContains(page, f'data-recap="{self.night.pk}:{self.two.host.user_id}"')
        self.assertContains(page, 'View session recap')
        self.assertContains(page, '>Final</span>')

    def test_recap_sums_frozen_buy_ins_and_handles_unknown_time(self):
        self.close()
        # One of the two finalized sets has a timer; the other recorded none.
        with patch('settlement.queries.clock.seconds_by_set', side_effect=lambda ids: {ids[0]: 60}):
            recap = queries.night_recap(self.night, queries.night_outcome(self.night).standings)
        self.assertEqual(recap['total_buy_in'], 500000)
        self.assertEqual(recap['play_seconds'], 60)
        self.assertTrue(recap['partial_time'])
        self.assertEqual([s.member.display_name for s in recap['winners']], ['A'])
        with patch('web.views.clock.timers', return_value={}):
            page = self.client.get(self.url)
        self.assertContains(page, 'Not recorded')
        self.assertNotContains(page, 'Your session result')  # host did not play

    def test_canceled_set_does_not_enter_recap(self):
        two = TwoSets(finalize_second=False)
        games.transition(two.second.pk, two.host, 'cancel', 'Synthetic cancellation')
        services.close_night(two.night_id, two.host)
        night = GameNight.objects.get(pk=two.night_id)
        with patch('settlement.queries.clock.seconds_by_set', side_effect=lambda ids: {i: 90 for i in ids}) as timer:
            recap = queries.night_recap(night, queries.night_outcome(night).standings)
        timer.assert_called_once()
        self.assertEqual(len(timer.call_args.args[0]), 1)  # the finalized set only
        self.assertEqual((recap['total_buy_in'], recap['play_seconds']), (250000, 90))

    def test_chips_break_even_recap_has_no_percentage_or_peso(self):
        one = Night('A', unit='chips')
        one.buy('A', 1000)
        one.go('reconciliation')
        one.cash('A', 1000)
        services.finalize(one.session.pk, one.host)
        services.close_night(one.session.night_id, one.host)
        self.client.force_login(one.host.user)
        page = self.client.get(reverse('night', args=[one.session.night_id]))
        self.assertContains(page, 'Everyone broke even.')
        self.assertContains(page, 'Nobody owes anything.')
        self.assertNotContains(page, '<progress')
        self.assertNotContains(page, '₱')

    def test_top_result_keeps_all_ties_and_session_tokens_are_member_scoped(self):
        standings = queries.night_outcome(self.night).standings
        standings[1].net = standings[0].net
        recap = queries.night_recap(self.night, standings)
        self.assertEqual([s.member.display_name for s in recap['winners']], ['A', 'B'])
        self.assertEqual([s.join_order for s in standings], [1, 2, 3])
        self.assertEqual([s.pk for s in standings], [s.member.pk for s in standings])

    def test_settle_up_leads_with_who_pays_whom_and_a_written_settled_state(self):
        self.close()
        page = self.client.get(self.url).content.decode()
        self.assertLess(page.index('Who pays whom'), page.index('Session results'))
        self.assertIn('class="badge badge-warn">Not paid', page)
        self.assertNotIn('settled-figure', page)
        for transfer in queries.night_outcome(self.night).transfers:
            services.mark_paid(self.night.pk, self.two.host, transfer.pk, uuid.uuid4())
        page = self.client.get(self.url).content.decode()
        self.assertIn('settled-figure', page)
        self.assertIn('data-still-to-pay="0"', page)
        self.assertIn('Nothing is left to pay.', page)
        self.assertIn('value="30000" max="30000"', page)
        self.assertNotIn('>Mark paid<', page)

    def test_player_sees_transfers_without_payment_actions(self):
        self.close()
        from groups.tests.helpers import add_player
        self.client.force_login(add_player(self.two.host.group, 'viewer').user)
        page = self.client.get(self.url).content.decode()
        self.assertIn('Who pays whom', page)
        self.assertIn('Not paid', page)
        self.assertNotIn('Mark paid', page)
