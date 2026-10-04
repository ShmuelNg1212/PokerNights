"""The stack check is a read model, independent of the cash-out balance gate."""
import uuid
from django.test import TestCase
from ledger import queries, services
from ledger.tests.helpers import Night
from ledger.tests.test_counts import count


class CountTotalTests(TestCase):
    def game(self, unit='php'):
        n = Night('A', 'B', 'Watcher', unit=unit)
        n.buy('A', 1000)
        n.buy('B', 1000)
        return n

    def test_missing_is_not_zero_and_money_free_players_do_not_count(self):
        n = self.game()
        n.go('reconciliation')
        count(n, 'A', 2000)
        total = queries.count_total(n.session)
        self.assertEqual((total.accounted, total.missing), (200000, 1))
        self.assertFalse(total.matches)
        self.assertEqual(total.status_text, 'Total matches so far; finish counting.')
        count(n, 'B', 0)
        self.assertTrue(queries.count_total(n.session).matches)
        self.assertFalse(queries.balance(n.session).ok)  # not cash-outs

    def test_partial_then_final_cash_out_never_double_counts(self):
        n = self.game()
        n.cash('A', 200)
        n.go('reconciliation')
        a = count(n, 'A', 800)
        count(n, 'B', 1000)
        before = queries.count_total(n.session)
        self.assertEqual((before.remaining, before.accounted, before.difference), (180000, 200000, 0))
        services.cash_out_counted(n.session.pk, n.host, [a.pk], uuid.uuid4())
        after = queries.count_total(n.session)
        self.assertEqual((after.remaining, after.accounted, after.missing), (100000, 200000, 0))
        self.assertTrue(after.matches)

    def test_superseded_and_cleared_counts_are_excluded(self):
        n = self.game()
        n.go('reconciliation')
        count(n, 'A', 500)
        count(n, 'A', 700)
        self.assertEqual(queries.count_total(n.session).remaining, 70000)
        services.clear_count(n.session.pk, n.host, n.players['A'].pk)
        total = queries.count_total(n.session)
        self.assertEqual((total.remaining, total.missing), (0, 2))

    def test_reversed_cash_out_and_linked_count_are_excluded(self):
        n = self.game()
        partial = n.cash('A', 200)
        services.reverse_cash_out(n.session.pk, n.host, partial.pk, 'Synthetic correction')
        n.go('reconciliation')
        a = count(n, 'A', 1000)
        services.cash_out_counted(n.session.pk, n.host, [a.pk], uuid.uuid4())
        final = n.line('A').cash_outs[-1]
        services.reverse_cash_out(n.session.pk, n.host, final.pk, 'Synthetic recount')
        total = queries.count_total(n.session)
        self.assertEqual((total.accounted, total.missing), (0, 2))

    def test_reversed_buy_in_and_stray_cash_out_prevent_match(self):
        n = self.game()
        n.go('reconciliation')
        n.cash('A', 1000)
        buy_in = n.line('A').buy_ins[0]
        services.reverse_buy_in(n.session.pk, n.host, buy_in.pk, 'Synthetic correction')
        count(n, 'B', 0)
        total = queries.count_total(n.session)
        self.assertEqual((total.accounted, total.summary.total), (100000, 100000))
        self.assertTrue(total.stray)
        self.assertFalse(total.complete)
        self.assertIn('without a buy-in', total.status_text)

    def test_overrides_do_not_hide_raw_missing_amount(self):
        n = self.game()
        n.go('reconciliation')
        n.cash('A', 900)
        n.cash('B', 1000)
        services.record_override(n.session.pk, n.host, 'Synthetic lost stack', 'player', n.players['A'].pk, uuid.uuid4())
        total = queries.count_total(n.session)
        self.assertTrue(total.has_overrides)
        self.assertEqual(total.status_text, '₱100 missing.')
        self.assertFalse(total.matches)
        self.assertTrue(queries.balance(n.session).ok)

    def test_empty_game_does_not_match(self):
        n = Night('Watcher', state='reconciliation')
        total = queries.count_total(n.session)
        self.assertFalse(total.complete)
        self.assertEqual(total.status_text, 'No buy-ins recorded.')

    def test_chips_and_extra_amount_use_native_format(self):
        n = self.game('chips')
        n.go('reconciliation')
        count(n, 'A', 2001)
        count(n, 'B', 0)
        total = queries.count_total(queries.summary(n.session))
        self.assertEqual(total.accounted, 2001)
        self.assertEqual(total.status_text, '1 chip extra.')
