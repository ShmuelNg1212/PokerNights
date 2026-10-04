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
