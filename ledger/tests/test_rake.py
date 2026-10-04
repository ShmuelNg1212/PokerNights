import uuid
from unittest.mock import patch

from django.test import TestCase
from audit.models import AuditEvent
from games import services as games
from groups.errors import RuleError
from ledger import queries, services
from ledger.models import BuyIn, RakeEntry
from .helpers import Night


def configure(night, **rule):
    return games.update_settings(night.session.pk, night.host,
                                 {**games.current_settings(night.session).stakes(), **rule}, request_id=uuid.uuid4())


class RakeTests(TestCase):
    def test_percentage_rebuy_retry_and_reversal(self):
        n = Night('A')
        configure(n, rake_mode='percent', rake_basis_points=500)
        request = uuid.uuid4()
        first = n.buy('A', 1000, request)
        n.buy('A', 1000, request)
        second = n.buy('A', 500)
        self.assertEqual((first.rake_amount, first.playable_amount), (5000, 95000))
        self.assertEqual(RakeEntry.objects.count(), 2)
        self.assertEqual(queries.group_rake(n.group)[0], {'php': 7500, 'chips': 0})
        services.reverse_buy_in(n.session.pk, n.host, second.pk, 'duplicate')
        self.assertEqual(queries.group_rake(n.group)[0]['php'], 5000)
        self.assertEqual(RakeEntry.objects.count(), 2)

    def test_each_chip_fee_rounds_down_separately_and_explicit_zero(self):
        n = Night('A', unit='chips', min_buy_in=1, default_buy_in=100, max_buy_in=10000)
        configure(n, rake_mode='percent', rake_basis_points=500)
        for amount, expected in ((101, 5), (19, 0), (19, 0), (10000, 500)):
            self.assertEqual(n.buy('A', amount).rake_amount, expected)
        self.assertEqual(queries.group_rake(n.group)[0], {'php': 0, 'chips': 505})

    def test_flat_guard_precedes_money_and_audit_and_clock_writes(self):
        n = Night('A')
        configure(n, rake_mode='flat', rake_flat=100000)
        before = (n.refresh().version, AuditEvent.objects.count(), n.session.play_intervals.count())
        with self.assertRaisesMessage(RuleError, 'positive amount in play'):
            n.buy('A', 1000)
        self.assertEqual(BuyIn.objects.count(), 0)
        self.assertEqual(RakeEntry.objects.count(), 0)
        self.assertEqual((n.refresh().version, AuditEvent.objects.count(), n.session.play_intervals.count()), before)
        self.assertEqual(n.buy('A', 1001).rake_amount, 100000)

    def test_failure_rolls_back_entire_opening_start(self):
        n = Night('A', 'B', state='open')
        configure(n, rake_mode='flat', rake_flat=2000)
        with patch('ledger.services.RakeEntry.objects.create', side_effect=RuntimeError('fault')):
            with self.assertRaises(RuntimeError):
                games.transition(n.session.pk, n.host, 'start')
        self.assertEqual(n.refresh().state, 'open')
        self.assertFalse(n.session.play_periods.exists())
        self.assertFalse(BuyIn.objects.exists())
        self.assertFalse(AuditEvent.objects.filter(action='buy_in.recorded').exists())

    def test_opening_and_late_manual_buy_ins_share_rule(self):
        n = Night('A', 'B', state='open')
        configure(n, rake_mode='flat', rake_flat=2000)
        request = uuid.uuid4()
        games.transition(n.session.pk, n.host, 'start', request_id=request)
        games.transition(n.session.pk, n.host, 'start', request_id=request)
        games.add_new_player(n.session.pk, n.host, 'C', uuid.uuid4())
        c = n.session.participants.get(member__display_name='C')
        services.record_buy_in(n.session.pk, n.host, c.pk, 100000, uuid.uuid4())
        self.assertEqual(queries.group_rake(n.group)[0]['php'], 6000)
        self.assertEqual(RakeEntry.objects.count(), 3)

    def test_rule_lock_retry_stakes_change_and_all_reversed_reconfigure(self):
        n = Night('A')
        request = uuid.uuid4()
        data = {**games.current_settings(n.session).stakes(), 'rake_mode': 'percent', 'rake_basis_points': 500}
        version = games.update_settings(n.session.pk, n.host, data, request_id=request)
        buy = n.buy('A', 1000)
        self.assertEqual(games.update_settings(n.session.pk, n.host, data, request_id=request).pk, version.pk)
        with self.assertRaisesMessage(RuleError, 'rake cannot change'):
            configure(n, rake_mode='off')
        games.update_settings(n.session.pk, n.host, {**version.stakes(), 'max_buy_in': 300000})
        self.assertEqual(n.buy('A', 3000).rake_amount, 15000)
        for b in BuyIn.objects.all():
            services.reverse_buy_in(n.session.pk, n.host, b.pk, 'called off')
        configure(n, rake_mode='off')
        self.assertEqual(queries.group_rake(n.group)[0]['php'], 0)
        self.assertEqual(n.buy('A', 1000).rake_amount, 0)

    def test_next_set_inherits_and_unit_change_resets(self):
        n = Night('A')
        configure(n, rake_mode='flat', rake_flat=2000)
        n.go('reconciliation')
        next_set = games.start_next_set(n.session.night_id, n.host)
        self.assertEqual(games.current_settings(next_set).rake_flat, 2000)
        other = Night('A')
        v = configure(other, rake_mode='flat', rake_flat=2000)
        updated = games.update_settings(other.session.pk, other.host, {**v.stakes(), 'unit': 'chips'})
        self.assertEqual(updated.rake_mode, 'off')

    def test_invalid_rules_and_historical_missing_entry(self):
        n = Night('A')
        for rule in ({'rake_mode': 'bad'}, {'rake_mode': 'percent', 'rake_basis_points': True},
                     {'rake_mode': 'percent', 'rake_basis_points': 10000}, {'rake_mode': 'flat', 'rake_flat': 0}):
            with self.assertRaises(RuleError):
                configure(n, **rule)
        b = BuyIn.objects.create(session=n.session, participant=n.players['A'], settings_version=games.current_settings(n.session),
                                 amount=100000, request_id=uuid.uuid4(), recorded_by=n.host.user)
        self.assertEqual((b.rake_amount, b.playable_amount), (0, 100000))
        self.assertEqual(queries.group_rake(n.group)[0], {'php': 0, 'chips': 0})

class RakeBalanceTests(TestCase):
    def finish(self, n, **cash):
        from settlement import services as settle
        n.go('reconciliation')
        for name, amount in cash.items():
            n.cash(name, amount)
        return settle.finalize(n.session.pk, n.host)

    def test_equal_after_rake_losses_create_no_transfers(self):
        from settlement import services as settle, queries as outcomes
        n = Night('A', 'B')
        configure(n, rake_mode='percent', rake_basis_points=500)
        n.buy('A', 1000); n.buy('B', 1000)
        s = queries.summary(n.session)
        self.assertEqual((s.total, s.rake, s.playable, s.in_play), (200000, 10000, 190000, 190000))
        f = self.finish(n, A=950, B=950)
        self.assertEqual((f.total_buy_in, f.total_cash_out, f.total_rake), (200000, 190000, 10000))
        results = list(f.results.all())
        self.assertEqual([r.net for r in results], [-5000, -5000])
        self.assertEqual([r.rake_total for r in results], [5000, 5000])
        self.assertEqual(sum(r.net for r in results) + f.total_rake, 0)
        plan = settle.close_night(n.session.night_id, n.host)
        self.assertFalse(plan.transfers.exists())
        recap = outcomes.night_recap(n.session.night, outcomes.night_outcome(n.session.night).standings)
        self.assertFalse(recap['all_even'])
        self.assertEqual(recap['total_rake'], 10000)

    def test_partial_cash_out_counts_and_missing_player_coverage(self):
        n = Night('A', 'B')
        configure(n, rake_mode='flat', rake_flat=2000)
        n.buy('A', 1000); n.buy('B', 1000)
        n.cash('A', 100)
        # A plays on: this is a partial cash-out.
        games.set_left(n.session.pk, n.host, n.players['A'].pk, left=False)
        services.back_in_play(n.players['A'], n.host)
        n.go('reconciliation')
        services.confirm_count(n.session.pk, n.host, n.players['A'].pk, 88000, uuid.uuid4())
        total = queries.count_total(n.session)
        self.assertEqual((total.remaining, total.accounted, total.missing), (88000, 102000, 1))
        self.assertFalse(total.complete)
        services.confirm_count(n.session.pk, n.host, n.players['B'].pk, 98000, uuid.uuid4())
        self.assertTrue(queries.count_total(n.session).matches)
        services.cash_out_counted(n.session.pk, n.host,
                                  list(n.session.final_counts.filter(is_current=True).values_list('pk', flat=True)), uuid.uuid4())
        self.assertTrue(queries.balance(n.session).ok)
        from settlement import services as settle
        f = settle.finalize(n.session.pk, n.host)
        self.assertEqual(f.total_rake, 4000)

    def test_override_covers_only_discrepancy_and_frozen_constraint(self):
        from django.db import IntegrityError, transaction
        from settlement import services as settle
        n = Night('A', 'B')
        configure(n, rake_mode='percent', rake_basis_points=500)
        n.buy('A', 1000); n.buy('B', 1000)
        n.go('reconciliation'); n.cash('A', 900); n.cash('B', 950)
        self.assertEqual(queries.balance(n.session).difference, -5000)
        with self.assertRaises(RuleError):
            settle.finalize(n.session.pk, n.host)
        services.record_override(n.session.pk, n.host, 'missing stack', 'equal', None, uuid.uuid4())
        f = settle.finalize(n.session.pk, n.host)
        self.assertEqual((f.raw_difference, f.total_rake), (-5000, 10000))
        self.assertEqual(sum(r.net for r in f.results.all()), -10000)
        with self.assertRaises(IntegrityError), transaction.atomic():
            type(f).objects.filter(pk=f.pk).update(total_rake=0)

    def test_mixed_sets_transfers_payments_and_group_isolation(self):
        from settlement import services as settle
        n = Night('A', 'B')
        configure(n, rake_mode='flat', rake_flat=2000)
        n.buy('A', 1000); n.buy('B', 1000)
        self.finish(n, A=1480, B=480)
        next_set = games.start_next_set(n.session.night_id, n.host)
        games.update_settings(next_set.pk, n.host, {**games.current_settings(next_set).stakes(), 'rake_mode': 'off'}, request_id=uuid.uuid4())
        players = {p.member.display_name: p for p in next_set.participants.select_related('member')}
        for p in players.values():
            services.record_buy_in(next_set.pk, n.host, p.pk, 100000, uuid.uuid4())
        games.transition(next_set.pk, n.host, 'start', opening_buy_ins=False)
        games.transition(next_set.pk, n.host, 'end')
        services.record_cash_out(next_set.pk, n.host, players['A'].pk, 90000, uuid.uuid4())
        services.record_cash_out(next_set.pk, n.host, players['B'].pk, 110000, uuid.uuid4())
        settle.finalize(next_set.pk, n.host)
        plan = settle.close_night(n.session.night_id, n.host)
        transfer = plan.transfers.get()
        self.assertEqual((transfer.payer_id, transfer.payee_id, transfer.amount),
                         (n.players['B'].member_id, n.players['A'].member_id, 40000))
        self.assertEqual(queries.group_rake(n.group)[0]['php'], 4000)
        settle.mark_paid(n.session.night_id, n.host, transfer.pk, uuid.uuid4())
        settle.mark_unpaid(n.session.night_id, n.host, transfer.pk)
        self.assertEqual(queries.group_rake(n.group)[0]['php'], 4000)
        other = Night('C', unit='chips')
        configure(other, rake_mode='flat', rake_flat=10)
        other.buy('C', 1000)
        self.assertEqual(queries.group_rake(other.group)[0], {'php': 0, 'chips': 10})
        totals, rows = queries.group_rake(n.group)
        self.assertEqual(sum(row['total'] for row in rows), totals['php'])
