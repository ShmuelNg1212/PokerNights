"""Debt balances through the public read API; integer amounts are worked examples."""
import uuid

from django.test import TestCase

from games.models import GameNight
from settlement import queries
from settlement.models import Clearance, ClearedTransfer
from settlement.tests.test_carried import Club


class DebtQueryTests(TestCase):
    def setUp(self):
        self.club = Club('Ana', 'Ben', 'Carlo')
        self.ana, self.ben, self.carlo = self.club.members.values()

    def rows(self, viewer=None):
        return queries.debts(self.club.group, viewer or self.club.host)

    def test_opposite_directions_net_by_pair_without_mixing_units_or_other_people(self):
        self.club.closed({'Ana': -500, 'Ben': 500})
        self.club.closed({'Ana': 300, 'Ben': -300})
        self.club.closed({'Ana': -50, 'Ben': 50}, unit='chips')
        self.club.closed({'Ben': -70, 'Carlo': 70})
        rows = self.rows(self.ana)
        self.assertEqual([(r.unit, r.net, len(r.transfers)) for r in rows], [('php', 20000, 2), ('chips', 50, 1)])
        self.assertEqual(len(self.rows()), 3)

    def test_same_direction_sums_and_exact_cancel_remains_visible(self):
        self.club.closed({'Ana': -500, 'Ben': 500})
        self.assertEqual(self.rows()[0].net, 50000)
        self.club.closed({'Ana': -100, 'Ben': 100})
        self.assertEqual(self.rows()[0].net, 60000)
        self.club.closed({'Ana': 600, 'Ben': -600})
        self.assertEqual(self.rows()[0].net, 0)

    def test_archived_paid_carried_and_cleared_are_not_debts(self):
        from settlement import services
        first = self.club.closed({'Ana': -500, 'Ben': 500})
        transfer = self.club.unpaid(first)[0]
        services.mark_paid(first, self.club.host, transfer.pk, uuid.uuid4())
        self.assertEqual(self.rows(), [])
        services.mark_unpaid(first, self.club.host, transfer.pk)
        second = self.club.play({'Ana': 500, 'Ben': -500})
        self.club.close(second, [transfer])
        self.assertEqual(self.rows(), [])
        third = self.club.closed({'Ana': -100, 'Ben': 100})
        clearance = Clearance.objects.create(group=self.club.group, unit='php', payer=self.ana, payee=self.ben,
            amount=10000, recorded_by=self.club.host.user, request_id=uuid.uuid4())
        ClearedTransfer.objects.create(clearance=clearance, transfer=self.club.unpaid(third)[0])
        self.assertEqual(self.rows(), [])
        fourth = self.club.closed({'Ana': -60, 'Ben': 60})
        from django.utils import timezone
        GameNight.objects.filter(pk=fourth).update(archived_at=timezone.now())
        self.assertEqual(self.rows(), [])

    def test_query_count_is_constant_as_sessions_grow(self):
        self.club.closed({'Ana': -500, 'Ben': 500})
        with self.assertNumQueries(1):
            self.rows()
        for _ in range(3):
            self.club.closed({'Ana': -100, 'Ben': 100})
        with self.assertNumQueries(1):
            rows = self.rows()
            self.assertEqual(rows[0].net, 80000)
            self.assertEqual(rows[0].transfers[0].payer.display_name, 'Ana')

    def test_cleared_transfers_are_done_on_each_session_and_cannot_carry(self):
        first = self.club.closed({'Ana': -500, 'Ben': 500})
        second = self.club.play({'Ana': 500, 'Ben': -500})
        transfer = self.club.unpaid(first)[0]
        clearance = Clearance.objects.create(group=self.club.group, unit='php', payer=self.ana, payee=self.ben,
            amount=50000, recorded_by=self.club.host.user, request_id=uuid.uuid4())
        ClearedTransfer.objects.create(clearance=clearance, transfer=transfer)
        state = queries.settle_states([first])[first]
        self.assertEqual((state.status, state.cleared, state.cleared_amount, state.still_to_pay), ('settled', 1, 50000, 0))
        outcome = queries.night_outcome(GameNight.objects.get(pk=first))
        self.assertEqual((outcome.status, outcome.cleared_count, outcome.cleared_amount, outcome.still_to_pay), ('settled', 1, 50000, 0))
        self.assertEqual(outcome.part_for(self.ana.pk).kind, 'settled')
        self.assertEqual(outcome.transfers[0].cleared.pk, clearance.pk)
        self.assertEqual(queries.unpaid_in(GameNight.objects.get(pk=first)), [])
        self.assertEqual(queries.carryable(GameNight.objects.get(pk=second)), [])

    def test_rake_fund_rows_stay_separate_and_visible_only_to_payer_or_host(self):
        from settlement.tests.test_rake_fund import raked, to_fund, finish
        from settlement import services
        n = raked('A', 'B')
        to_fund(n)
        n.buy('A', 1000); n.buy('B', 1000)
        finish(n, A=1400, B=500)
        services.close_night(n.session.night_id, n.host)
        rows = queries.debts(n.group, n.host)
        fund = [r for r in rows if r.member_b is None]
        self.assertEqual(len(fund), 1)
        self.assertTrue(fund[0].transfers[0].to_rake_fund)
        payer = fund[0].member_a
        self.assertTrue(any(r.member_b is None for r in queries.debts(n.group, payer)))
        other = n.players['A' if payer.display_name == 'B' else 'B'].member
        self.assertFalse(any(r.member_b is None for r in queries.debts(n.group, other)))
