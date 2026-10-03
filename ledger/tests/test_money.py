import random

from django.test import SimpleTestCase

from ledger import money
from ledger.money import MoneyError


class ParseAndFormatTests(SimpleTestCase):
    def test_parse_accepts_common_input(self):
        cases = {"1000": 100000, "1,000": 100000, "₱1,000.50": 100050, " 250.5 ": 25050, "0": 0, "PHP 20": 2000}
        for text, centavos in cases.items():
            self.assertEqual(money.parse_pesos(text), centavos, text)

    def test_parse_refuses_bad_input(self):
        for text in ["", "abc", "1.005", "-5", "NaN", "Infinity", "1e400", "99999999999999"]:
            with self.assertRaises(MoneyError, msg=text):
                money.parse_pesos(text)

    def test_parse_never_returns_a_float(self):
        self.assertIsInstance(money.parse_pesos("0.10"), int)
        self.assertEqual(money.parse_pesos("0.10") + money.parse_pesos("0.20"), 30)

    def test_format(self):
        self.assertEqual(money.format_pesos(160000), "₱1,600")
        self.assertEqual(money.format_pesos(160050), "₱1,600.50")
        self.assertEqual(money.format_pesos(5), "₱0.05")
        self.assertEqual(money.format_pesos(-30000), "−₱300")
        self.assertEqual(money.format_signed(60000), "+₱600")
        self.assertEqual(money.format_signed(-30000), "−₱300")
        self.assertEqual(money.format_signed(0), "₱0")


class SplitEqualTests(SimpleTestCase):
    def test_even_split(self):
        self.assertEqual(money.split_equal(900, 3), [300, 300, 300])

    def test_uneven_split_gives_the_extra_to_the_first_parts(self):
        self.assertEqual(money.split_equal(500, 3), [167, 167, 166])
        self.assertEqual(money.split_equal(-500, 3), [-167, -167, -166])
        self.assertEqual(money.split_equal(2, 3), [1, 1, 0])

    def test_split_always_sums_to_the_total(self):
        rng = random.Random(7)
        for _ in range(300):
            total, shares = rng.randint(-10**6, 10**6), rng.randint(1, 12)
            parts = money.split_equal(total, shares)
            self.assertEqual(sum(parts), total)
            self.assertLessEqual(max(parts) - min(parts), 1)
        with self.assertRaises(MoneyError):
            money.split_equal(100, 0)


class UnitAmountTests(SimpleTestCase):
    def test_pesos_parse_and_format_as_before(self):
        self.assertEqual(money.parse_amount("1,600.50", money.PHP), 160050)
        self.assertEqual(money.format_amount(160050, money.PHP), "₱1,600.50")
        self.assertEqual(money.format_signed_amount(60000, money.PHP), "+₱600")
        self.assertEqual(money.plain_amount(160050, money.PHP), "1600.50")

    def test_chips_are_whole_numbers_with_no_peso_sign(self):
        self.assertEqual(money.parse_amount("1,500", money.CHIPS), 1500)
        self.assertEqual(money.parse_amount(" 20 chips ", money.CHIPS), 20)
        self.assertEqual(money.parse_amount("0", money.CHIPS), 0)
        self.assertEqual(money.format_amount(1600, money.CHIPS), "1,600 chips")
        self.assertEqual(money.format_amount(1, money.CHIPS), "1 chip")
        self.assertEqual(money.format_amount(-300, money.CHIPS), "−300 chips")
        self.assertEqual(money.format_signed_amount(600, money.CHIPS), "+600 chips")
        self.assertEqual(money.format_signed_amount(0, money.CHIPS), "0 chips")
        self.assertEqual(money.plain_amount(1600, money.CHIPS), "1600")
        self.assertNotIn("₱", money.format_amount(1600, money.CHIPS))

    def test_chip_input_with_decimals_or_signs_is_refused(self):
        for text in ["10.5", "-5", "", "abc", "₱100", "1e3", "99999999999999"]:
            with self.assertRaises(MoneyError, msg=text):
                money.parse_amount(text, money.CHIPS)

    def test_amounts_are_always_integers(self):
        for unit in money.UNITS:
            self.assertIsInstance(money.parse_amount("25", unit), int)
