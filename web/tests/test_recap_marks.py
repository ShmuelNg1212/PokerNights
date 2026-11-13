"""The recap's Highlights say what a closed session meant in a player's history. Good news or a count; never a loss."""

import datetime
from unittest import mock

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from settlement.tests.test_stats import Club

START = datetime.date(2026, 1, 1)
WIN, LOSE, EVEN = (1000, 1500), (1000, 500), (1000, 1000)


class RecapMarksTests(TestCase):
    def setUp(self):
        self.club = Club()
        self.client.force_login(self.club.host.user)
        self.count = 0

    def session(self, figures, **kwargs):
        day = START + datetime.timedelta(days=7 * self.count)
        self.count += 1
        return self.club.session(day, figures, **kwargs)

    def recap(self, session):
        html = self.client.get(reverse("night", args=[session.night_id])).content.decode()
        if 'class="sheet-content recap"' not in html:
            return ""
        start = html.index('class="sheet-content recap"')
        return html[start:html.index("recap-sets-title", start)]

    def rows(self, recap):
        """Each mark's kind, in the order shown."""
        return [part.split('"')[0] for part in recap.split('data-mark="')[1:]]

    def test_a_third_winning_session_in_a_row_is_said_with_the_player(self):
        for _ in range(2):
            self.session({"Ana": WIN, "Bong": LOSE})
        recap = self.recap(self.session({"Ana": WIN, "Bong": LOSE}))
        self.assertEqual(self.rows(recap), ["run"])
        row = recap[recap.index('data-mark="run"'):]
        self.assertIn("Winning run", row)
        self.assertIn('<span class="recap-who">Ana</span>', row)
        self.assertIn("3 in a row", row)

    def test_a_losing_run_is_not_named(self):
        for _ in range(2):
            self.session({"Ana": WIN, "Bong": LOSE})
        recap = self.recap(self.session({"Ana": WIN, "Bong": LOSE}))
        marks = recap[recap.index("recap-notes-title"):]
        self.assertNotIn("Bong", marks)
        self.assertNotIn("Lost", marks)
        self.assertNotIn("losing", marks.lower())

    def test_a_first_session_has_no_marks_and_no_empty_highlights(self):
        recap = self.recap(self.session({"Ana": WIN, "Bong": LOSE}))
        self.assertTrue(recap)
        self.assertEqual(self.rows(recap), [])
        self.assertNotIn("recap-notes-title", recap)

    def test_the_marks_follow_their_order_with_exact_amounts(self):
        self.session({"Ana": WIN, "Bong": LOSE, "Caloy": EVEN})
        self.session({"Ana": WIN, "Bong": LOSE, "Caloy": EVEN})
        recap = self.recap(self.session({"Ana": (1000, 1200), "Bong": (1000, 1300), "Caloy": (1000, 500)}))
        self.assertEqual(self.rows(recap), ["run", "first_win"])
        first = recap[recap.index('data-mark="first_win"'):]
        self.assertIn("First win", first)
        self.assertIn("Bong", first)
        self.assertIn("+₱300<", first)
        self.assertIn("amount plus", first)

    def test_a_personal_best_shows_its_signed_amount(self):
        self.session({"Ana": (1000, 1100), "Bong": (1000, 900)})
        self.session({"Ana": LOSE, "Bong": WIN})
        recap = self.recap(self.session({"Ana": (1000, 1800), "Bong": (1000, 200)}))
        self.assertEqual(self.rows(recap), ["best"])
        row = recap[recap.index('data-mark="best"'):]
        self.assertIn("Personal best", row)
        self.assertIn("+₱800", row)

    def test_players_with_the_same_round_number_share_a_row(self):
        for _ in range(9):
            self.session({"Bong": EVEN, "Ana": EVEN})
        recap = self.recap(self.session({"Bong": EVEN, "Ana": EVEN}))
        self.assertEqual(self.rows(recap), ["round"])
        row = recap[recap.index('data-mark="round"'):]
        self.assertIn("10th session", row)
        self.assertLess(row.index("Ana"), row.index("Bong"))

    def test_a_chips_session_reads_only_chips_sessions(self):
        self.session({"Ana": WIN, "Bong": LOSE})
        self.session({"Ana": WIN, "Bong": LOSE})
        recap = self.recap(self.session({"Ana": WIN, "Bong": LOSE}, unit="chips"))
        self.assertTrue(recap)
        self.assertEqual(self.rows(recap), [])

    def test_a_session_that_is_not_closed_has_no_recap_and_reads_no_marks(self):
        for _ in range(2):
            self.session({"Ana": WIN, "Bong": LOSE})
        with mock.patch("web.stats.recap_marks") as marks:
            self.assertEqual(self.recap(self.session({"Ana": WIN, "Bong": LOSE}, close=False)), "")
        marks.assert_not_called()

    def test_the_marks_cost_one_query(self):
        for _ in range(2):
            self.session({"Ana": WIN, "Bong": LOSE})
        url = reverse("night", args=[self.session({"Ana": WIN, "Bong": LOSE}).night_id])
        self.client.get(url)
        with CaptureQueriesContext(connection) as with_marks:
            self.client.get(url)
        with mock.patch("web.stats.recap_marks", return_value=[]), CaptureQueriesContext(connection) as without:
            self.client.get(url)
        self.assertEqual(len(with_marks) - len(without), 1)
