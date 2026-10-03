import random

from django.test import SimpleTestCase

from settlement.algorithm import balances, is_proven_minimal, settle


def apply(parties, transfers):
    """Balances left after the transfers are paid."""
    left = dict(parties)
    for payer, payee, amount in transfers:
        left[payer] += amount
        left[payee] -= amount
    return left


def brute_force_minimum(amounts):
    """The true minimum number of transfers, by exhaustive search (small inputs only)."""
    amounts = [a for a in amounts if a != 0]

    def search(start, values):
        while start < len(values) and values[start] == 0:
            start += 1
        if start == len(values):
            return 0
        best = len(values)
        for other in range(start + 1, len(values)):
            if values[other] * values[start] < 0:
                values[other] += values[start]
                best = min(best, 1 + search(start + 1, values))
                values[other] -= values[start]
        return best

    return search(0, list(amounts))


class WorkedExampleTests(SimpleTestCase):
    """A buys in ₱1,000 and ends with ₱1,600. B ₱1,000 → ₱700. C ₱500 → ₱200."""

    NETS = {"A": 60000, "B": -30000, "C": -30000}

    def order(self, found):
        return [(key, found.get(key, 0)) for key in ["bank", "A", "B", "C"] if key in found]

    def test_no_prior_payments(self):
        transfers = settle(self.order(balances(self.NETS)))
        self.assertEqual(transfers, [("B", "A", 30000), ("C", "A", 30000)])

    def test_a_prior_payment_changes_the_transfers_but_not_the_results(self):
        found = balances(self.NETS, [("C", "A", 20000)])
        self.assertEqual(found, {"A": 40000, "B": -30000, "C": -10000})
        self.assertEqual(settle(self.order(found)), [("B", "A", 30000), ("C", "A", 10000)])

    def test_early_leaver_who_paid_on_the_way_out_is_settled(self):
        found = balances(self.NETS, [("B", "A", 30000)])
        self.assertEqual(found["B"], 0)
        self.assertEqual(settle(self.order(found)), [("C", "A", 30000)])

    def test_banker_who_collected_every_buy_in_pays_the_cash_outs(self):
        paid = [("A", "bank", 100000), ("B", "bank", 100000), ("C", "bank", 50000)]
        found = balances(self.NETS, paid)
        self.assertEqual(found, {"A": 160000, "B": 70000, "C": 20000, "bank": -250000})
        self.assertEqual(
            settle(self.order(found)),
            [("bank", "A", 160000), ("bank", "B", 70000), ("bank", "C", 20000)],
        )

    def test_overpayment_flows_back(self):
        # B owed ₱300 but handed A ₱500, so B is now owed ₱200 and A only ₱100.
        found = balances(self.NETS, [("B", "A", 50000)])
        self.assertEqual(found, {"A": 10000, "B": 20000, "C": -30000})
        self.assertEqual(sorted(settle(self.order(found))), [("C", "A", 10000), ("C", "B", 20000)])


class SettleTests(SimpleTestCase):
    def test_nothing_to_settle(self):
        self.assertEqual(settle([]), [])
        self.assertEqual(settle([("A", 0), ("B", 0)]), [])

    def test_a_winner_paid_by_several_losers(self):
        transfers = settle([("W", 90000), ("L1", -20000), ("L2", -30000), ("L3", -40000)])
        self.assertEqual(len(transfers), 3)
        self.assertTrue(all(payee == "W" for _, payee, _ in transfers))
        self.assertEqual(sum(amount for _, _, amount in transfers), 90000)

    def test_two_independent_pairs_need_two_transfers_not_three(self):
        # A greedy largest-to-largest rule alone would use three transfers here.
        parties = [("A", 50000), ("B", 30000), ("C", -30000), ("D", -50000)]
        self.assertEqual(sorted(settle(parties)), [("C", "B", 30000), ("D", "A", 50000)])

    def test_zero_sum_groups_larger_than_pairs_are_found(self):
        # {+5, −2, −3} and {+7, −3, −4}: two groups, so 6 − 2 = 4 transfers.
        parties = [("a", 5), ("b", 7), ("c", -2), ("d", -3), ("e", -3), ("f", -4)]
        transfers = settle(parties)
        self.assertEqual(len(transfers), 4)
        self.assertTrue(all(v == 0 for v in apply(parties, transfers).values()))

    def test_ties_follow_the_given_order(self):
        first = settle([("A", 60000), ("B", -30000), ("C", -30000)])
        self.assertEqual(first, [("B", "A", 30000), ("C", "A", 30000)])
        self.assertEqual(first, settle([("A", 60000), ("B", -30000), ("C", -30000)]))

    def test_amounts_that_do_not_divide_evenly_stay_exact(self):
        parties = [("A", 10001), ("B", -3334), ("C", -3334), ("D", -3333)]
        transfers = settle(parties)
        self.assertTrue(all(v == 0 for v in apply(parties, transfers).values()))
        self.assertTrue(all(isinstance(amount, int) for _, _, amount in transfers))

    def test_input_must_sum_to_zero_and_be_integers(self):
        with self.assertRaises(ValueError):
            settle([("A", 100), ("B", -99)])
        with self.assertRaises(ValueError):
            settle([("A", 0.5), ("B", -0.5)])

    def test_random_inputs_clear_every_balance_within_the_bound(self):
        rng = random.Random(20261003)
        for _ in range(300):
            n = rng.randint(2, 12)
            amounts = [rng.randint(-200000, 200000) for _ in range(n - 1)]
            parties = [(i, a) for i, a in enumerate(amounts + [-sum(amounts)])]
            transfers = settle(parties)
            self.assertTrue(all(v == 0 for v in apply(parties, transfers).values()))
            self.assertTrue(all(amount > 0 and payer != payee for payer, payee, amount in transfers))
            open_count = sum(1 for _, a in parties if a)
            self.assertLessEqual(len(transfers), max(open_count - 1, 0))
            self.assertEqual(transfers, settle(parties))  # deterministic

    def test_transfer_count_equals_the_brute_force_minimum(self):
        rng = random.Random(465)
        for _ in range(400):
            n = rng.randint(2, 7)
            # Small values make zero-sum subgroups common, which is the hard case.
            amounts = [rng.randint(-6, 6) for _ in range(n - 1)]
            amounts.append(-sum(amounts))
            parties = list(enumerate(amounts))
            transfers = settle(parties)
            self.assertTrue(all(v == 0 for v in apply(parties, transfers).values()))
            self.assertEqual(len(transfers), brute_force_minimum(amounts), amounts)

    def test_a_full_table_with_a_banker_is_fast_and_exact(self):
        amounts = [1200, -300, 450, -800, 75, -75, 600, -900, 300, -550, 125, -125]
        parties = list(enumerate(amounts + [-sum(amounts)]))
        self.assertTrue(is_proven_minimal(parties))
        transfers = settle(parties)
        self.assertTrue(all(v == 0 for v in apply(parties, transfers).values()))

    def test_fallback_above_the_exact_limit_still_settles(self):
        amounts = [100] * 9 + [-100] * 9
        parties = list(enumerate(amounts))
        self.assertFalse(is_proven_minimal(parties))
        transfers = settle(parties)
        self.assertTrue(all(v == 0 for v in apply(parties, transfers).values()))
        self.assertLessEqual(len(transfers), 17)
