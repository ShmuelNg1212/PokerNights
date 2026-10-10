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
        self.assertEqual(recap.total_buy_in, 500000)
        self.assertEqual(recap.play_seconds, 60)
        self.assertTrue(recap.partial_time)
        self.assertEqual([s.member.display_name for s in recap.winners], ['A'])
        with patch('web.views.clock.timers', return_value={}):
            page = self.client.get(self.url)
        self.assertContains(page, 'Not recorded')
        self.assertNotContains(page, 'Your night')  # host did not play

    def test_canceled_set_does_not_enter_recap(self):
        two = TwoSets(finalize_second=False)
        games.transition(two.second.pk, two.host, 'cancel', 'Synthetic cancellation')
        services.close_night(two.night_id, two.host)
        night = GameNight.objects.get(pk=two.night_id)
        with patch('settlement.queries.clock.seconds_by_set', side_effect=lambda ids: {i: 90 for i in ids}) as timer:
            recap = queries.night_recap(night, queries.night_outcome(night).standings)
        timer.assert_called_once()
        self.assertEqual(len(timer.call_args.args[0]), 1)  # the finalized set only
        self.assertEqual((recap.total_buy_in, recap.play_seconds), (250000, 90))

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
        self.assertEqual([s.member.display_name for s in recap.winners], ['A', 'B'])
        self.assertEqual([s.join_order for s in standings], [1, 2, 3])
        self.assertEqual([s.pk for s in standings], [s.member.pk for s in standings])

    def test_settle_up_leads_with_who_pays_whom_and_a_written_settled_state(self):
        self.close()
        page = self.client.get(self.url).content.decode()
        self.assertLess(page.index('Who pays whom'), page.index('Session results'))
        self.assertIn('class="unpaid-word">Not paid', page)
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


class RecapPageTests(TestCase):
    """The closing recap as the session page draws it."""

    def setUp(self):
        self.two = TwoSets()
        services.close_night(self.two.night_id, self.two.host)
        self.url = reverse('night', args=[self.two.night_id])

    def page(self, user):
        self.client.force_login(user)
        return self.client.get(self.url)

    def test_host_who_did_not_play_sees_the_table_and_no_own_night(self):
        page = self.page(self.two.host.user)
        for heading in ('Top session result', "Everyone's results", 'Highlights', 'Set by set'):
            self.assertContains(page, heading)
        self.assertNotContains(page, 'Your night')
        self.assertNotContains(page, '(you)')
        self.assertContains(page, '₱2,000 in · ₱2,200 out · 2 buy-ins')
        self.assertContains(page, '₱1,000 in · ₱700 out · 2 buy-ins')  # the loss is listed
        self.assertContains(page, 'Biggest win in one set')
        self.assertContains(page, 'in set 1')
        self.assertNotContains(page, 'Most buy-ins')  # everyone bought in twice
        self.assertContains(page, '3 players · ₱2,500 bought in', count=2)
        self.assertContains(page, 'style="--share:100;--i:2"')
        self.assertNotContains(page, '%')

    def test_a_player_sees_their_own_night_and_their_transfer(self):
        from groups.tests.helpers import add_player
        from games.models import Participant
        night = Night('A')
        member = night.add_login_player('Ben')
        night.buy('A', 1000)
        night.buy('Ben', 1000)
        night.buy('Ben', 500)
        night.go('reconciliation')
        night.cash('A', 2000)
        night.cash('Ben', 500)
        services.finalize(night.session.pk, night.host)
        services.close_night(night.session.night_id, night.host)
        self.client.force_login(member.user)
        page = self.client.get(reverse('night', args=[night.session.night_id]))
        self.assertContains(page, 'Your night')
        self.assertContains(page, '₱1,500 bought in · ₱500 cashed out · 2 buy-ins')
        self.assertContains(page, 'You pay <strong>A</strong>')
        self.assertContains(page, 'Ben <span class="muted">(you)</span>')
        self.assertContains(page, 'Most buy-ins')
        self.assertNotContains(page, 'Biggest win in one set')  # one set
        self.assertNotContains(page, 'recap-by-set')


class SettlePageTests(TestCase):
    """The closed session page: a person's own part first, then one row per transfer."""

    def closed(self, ben_cash, a_cash):
        night = Night('A')
        self.ben = night.add_login_player('Ben')
        for name in ('A', 'Ben'):
            night.buy(name, 1000)
        night.go('reconciliation')
        night.cash('A', a_cash)
        night.cash('Ben', ben_cash)
        services.finalize(night.session.pk, night.host)
        services.close_night(night.session.night_id, night.host)
        self.host = night.host
        self.night_id = night.session.night_id
        self.url = reverse('night', args=[self.night_id])
        return night

    def page(self, user):
        self.client.force_login(user)
        return self.client.get(self.url).content.decode()

    def lead(self, html):
        return html[html.index('class="felt hero"'):html.index('</section>', html.index('class="felt hero"'))]

    def test_a_player_who_owes_reads_you_pay(self):
        self.closed(ben_cash=600, a_cash=1400)
        lead = self.lead(self.page(self.ben.user))
        self.assertIn('<h2 class="pot-label">You pay</h2>', lead)
        self.assertIn('data-my-part="pay:40000">₱400', lead)
        self.assertIn('You pay <strong>A</strong> <span class="amount">₱400</span> · Not paid', lead)
        self.assertIn('Table: ₱0 of ₱400 marked paid · 0 of 1 transfer', lead)
        self.assertNotIn('Still to pay', lead)
        self.assertNotIn('Collected rake', lead)
        self.assertIn('Your result in this session', lead)

    def test_a_player_who_is_owed_reads_you_receive_then_settled(self):
        self.closed(ben_cash=1400, a_cash=600)
        self.assertIn('data-my-part="receive:40000">₱400', self.lead(self.page(self.ben.user)))
        transfer = queries.night_outcome(GameNight.objects.get(pk=self.night_id)).transfers[0]
        services.mark_paid(self.night_id, self.host, transfer.pk, uuid.uuid4())
        lead = self.lead(self.page(self.ben.user))
        self.assertIn('data-my-part="settled:0"', lead)
        self.assertIn("You're settled", lead)
        self.assertIn('<strong>A</strong> pays you <span class="amount">₱400</span> · Paid', lead)
        self.assertIn('Nothing is left to pay.', lead)

    def test_a_player_with_no_transfer_reads_nothing_to_pay(self):
        self.closed(ben_cash=1000, a_cash=1000)
        lead = self.lead(self.page(self.ben.user))
        self.assertIn('data-my-part="none:0">Nothing to pay', lead)
        self.assertIn('You owe nothing and are owed nothing.', lead)
        self.assertIn('Nobody owes anything.', lead)
        self.assertNotIn('<progress', lead)

    def test_the_host_reads_the_table_total(self):
        self.closed(ben_cash=600, a_cash=1400)
        html = self.page(self.host.user)
        lead = self.lead(html)
        self.assertIn('<h2 class="pot-label">Still to pay</h2>', lead)
        self.assertIn('data-still-to-pay="40000"', lead)
        self.assertIn('₱0 of ₱400 marked paid · 0 of 1 transfer', lead)
        self.assertNotIn('data-my-part', lead)
        self.assertNotIn('Table:', lead)

    def test_a_transfer_is_one_row_and_own_rows_are_marked_in_place(self):
        self.closed(ben_cash=600, a_cash=1400)
        html = self.page(self.ben.user)
        row = html[html.index('class="transfer-row transfer-line'):]
        row = row[:row.index('</li>')]
        self.assertIn('transfer-line is-mine"', row)
        self.assertIn('<strong>Ben</strong> <span class="muted small">(you)</span>', row)
        self.assertIn('aria-label="Ben pays A"', row)
        self.assertNotIn('<form', row)
        host_row = self.page(self.host.user)
        host_row = host_row[host_row.index('class="transfer-row transfer-line'):]
        host_row = host_row[:host_row.index('</li>')]
        self.assertIn('transfer-line has-action"', host_row)
        self.assertIn('name="request_id"', host_row)
        self.assertIn('>Mark paid</button>', host_row)

    def test_order_of_the_page_and_folded_records(self):
        self.closed(ben_cash=600, a_cash=1400)
        transfer = queries.night_outcome(GameNight.objects.get(pk=self.night_id)).transfers[0]
        services.mark_paid(self.night_id, self.host, transfer.pk, uuid.uuid4())
        html = self.page(self.host.user)
        marks = ['class="felt hero"', 'id="transfers-title"', 'id="results-title"', 'id="sets-title"', 'id="payments-title"',
                 'class="night-after"', 'data-sheet-open="recap"', 'id="manage"']
        order = [html.index(mark) for mark in marks]
        self.assertEqual(order, sorted(order))
        self.assertIn('<details class="night-records" data-key="payment-records"><summary><h2 id="payments-title">Payment records <span class="muted small">1</span>', html)
        self.assertIn('How this is worked out', html)
        self.assertIn('>Undo</button>', html)
        self.assertIn('<span class="paid-word">Paid</span>', html)
        self.assertIn('marked by the host', html)

    def test_an_open_session_keeps_its_overview(self):
        night = Night('A')
        night.buy('A', 1000)
        night.go('reconciliation')
        night.cash('A', 1000)
        services.finalize(night.session.pk, night.host)
        self.client.force_login(night.host.user)
        html = self.client.get(reverse('night', args=[night.session.night_id])).content.decode()
        self.assertNotIn('night-settle', html)
        self.assertIn('Session open', html)
        self.assertIn('Collected rake across sets', html)
        self.assertIn('Close session and settle up', html)
        self.assertNotIn('data-my-part', html)
