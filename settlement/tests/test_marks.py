"""The marks of a night: what one closed session meant in each player's history. Read, never stored."""

import datetime

from django.test import SimpleTestCase, TestCase

from games import services as games
from settlement import stats
from settlement.stats import Mark, SessionResult, night_marks

from .test_stats import Club

D = datetime.date
START = D(2026, 1, 1)


def history(*sessions):
    """``sessions`` are ``{member id: net}``, one a week, oldest first. The session's id is its place, from 1."""
    rows = []
    for index, nets in enumerate(sessions):
        day = START + datetime.timedelta(days=7 * index)
        rows += [SessionResult(member, index + 1, day, "Main table", net, 1000, 0, 0, None) for member, net in nets.items()]
    return rows


def marks(*sessions, of=None):
    return night_marks(history(*sessions), of or len(sessions))


def kinds(found, member=1):
    return [mark.kind for mark in found if mark.member_id == member]


class WinningRunTests(SimpleTestCase):
    def test_three_winning_sessions_in_a_row_are_a_run(self):
        self.assertIn(Mark("run", 1, count=3), marks({1: 100}, {1: 50}, {1: 10}))

    def test_two_in_a_row_are_not(self):
        self.assertNotIn("run", kinds(marks({1: -5}, {1: 50}, {1: 10})))

    def test_the_run_counts_every_winning_session_back_to_the_last_other_result(self):
        self.assertIn(Mark("run", 1, count=4), marks({1: -5}, {1: 1}, {1: 1}, {1: 1}, {1: 1}))

    def test_a_break_even_session_ends_a_run(self):
        self.assertNotIn("run", kinds(marks({1: 100}, {1: 100}, {1: 0}, {1: 100}, {1: 100})))

    def test_a_session_the_player_missed_does_not_end_a_run(self):
        self.assertIn(Mark("run", 1, count=3), marks({1: 100, 2: -100}, {1: 50, 2: -50}, {2: 5, 3: -5}, {1: 10, 2: -10}))

    def test_a_losing_session_has_no_run_even_after_wins(self):
        self.assertNotIn("run", kinds(marks({1: 100}, {1: 100}, {1: 100}, {1: -1})))

    def test_the_longest_run_comes_first(self):
        found = marks({1: -1, 2: 9}, {1: 5, 2: 9}, {1: 5, 2: 9}, {1: 5, 2: 9})
        self.assertEqual([(m.member_id, m.count) for m in found if m.kind == "run"], [(2, 4), (1, 3)])


class PersonalBestTests(SimpleTestCase):
    def test_a_result_above_every_earlier_one_in_a_third_session(self):
        self.assertIn(Mark("best", 1, amount=300), marks({1: 100}, {1: -50}, {1: 300}))

    def test_two_sessions_are_too_few(self):
        self.assertNotIn("best", kinds(marks({1: 100}, {1: 300})))

    def test_a_tie_with_an_earlier_best_is_not_a_best(self):
        self.assertNotIn("best", kinds(marks({1: 300}, {1: -50}, {1: 300})))

    def test_the_smallest_loss_is_not_a_best(self):
        self.assertEqual(marks({1: -300}, {1: -200}, {1: -100}), [])

    def test_a_first_win_is_not_also_called_a_best(self):
        self.assertEqual(kinds(marks({1: -300}, {1: -200}, {1: 100})), ["first_win"])


class FirstWinTests(SimpleTestCase):
    def test_the_first_positive_result_after_other_sessions(self):
        self.assertIn(Mark("first_win", 1, amount=100), marks({1: -300}, {1: 0}, {1: 100}))

    def test_a_win_in_a_first_session_has_no_mark(self):
        self.assertEqual(marks({1: 100, 2: -100}), [])

    def test_a_second_win_is_not_a_first(self):
        self.assertNotIn("first_win", kinds(marks({1: 100}, {1: 50})))


class RoundNumberTests(SimpleTestCase):
    def played(self, count, net=-1):
        return marks(*[{1: net}] * count)

    def test_the_tenth_session_and_not_the_ninth(self):
        self.assertEqual(self.played(9), [])
        self.assertEqual(self.played(10), [Mark("round", 1, count=10)])

    def test_the_round_numbers(self):
        hits = [n for n in range(1, 260) if "round" in kinds(self.played(n))]
        self.assertEqual(hits, [10, 25, 50, 100, 150, 200, 250])

    def test_a_round_number_counts_a_losing_night_without_naming_the_loss(self):
        self.assertEqual(self.played(25, net=-500), [Mark("round", 1, count=25)])


class NightMarksTests(SimpleTestCase):
    def test_only_players_of_that_session_get_marks(self):
        found = marks({1: 1, 2: 1}, {1: 1, 2: 1}, {1: 1, 2: 1}, {1: 1})
        self.assertEqual({m.member_id for m in found}, {1})

    def test_sessions_after_the_one_asked_for_are_ignored(self):
        self.assertEqual(marks({1: 100}, {1: 50}, {1: 10}, {1: 999}, of=3), [Mark("run", 1, count=3)])
        self.assertEqual(marks({1: 100}, {1: 50}, {1: 10}, {1: 999}, of=2), [])

    def test_a_session_with_no_rows_has_no_marks(self):
        self.assertEqual(night_marks(history({1: 100}), 99), [])
        self.assertEqual(night_marks([], 1), [])

    def test_two_sessions_on_one_date_are_ordered_by_their_id(self):
        day = START
        rows = [SessionResult(1, n, day, "Main table", net, 1000, 0, 0, None) for n, net in ((1, 5), (2, 5), (3, 5))]
        self.assertEqual(night_marks(rows, 3), [Mark("run", 1, count=3)])
        self.assertEqual(night_marks(rows, 2), [])

    def test_the_order_is_runs_bests_first_wins_then_round_numbers(self):
        ten = [{1: 1, 2: -1, 3: -9, 4: 5}] * 7 + [{1: 1, 2: -1, 3: -9, 4: -5}] * 2 + [{1: 50, 2: 7, 3: -9, 4: 1}]
        found = marks(*ten)
        self.assertEqual([(m.kind, m.member_id) for m in found],
                         [("run", 1), ("best", 1), ("first_win", 2), ("round", 1), ("round", 2), ("round", 3), ("round", 4)])

    def test_no_mark_names_a_loss(self):
        ten = [{1: -100, 2: 100}] * 12
        for of in range(1, 13):
            for mark in marks(*ten, of=of):
                if mark.member_id == 1:
                    self.assertEqual(mark.kind, "round")
                    self.assertIsNone(mark.amount)
                self.assertTrue(mark.amount is None or mark.amount > 0)


class MarksFromFetchTests(TestCase):
    """Through the one query that Stats uses: closed sessions only, one unit, archived sessions left out."""

    def setUp(self):
        self.club = Club()
        self.days = [START + datetime.timedelta(days=7 * n) for n in range(4)]

    def marks(self, session, unit="php"):
        return night_marks(stats.fetch(self.club.group, unit), session.night_id)

    def test_a_run_across_three_closed_sessions(self):
        for day in self.days[:2]:
            self.club.session(day, {"A": (1000, 1500), "B": (1000, 500)})
        third = self.club.session(self.days[2], {"A": (1000, 1100), "B": (1000, 900)})
        a = self.club.member("A").pk
        self.assertEqual(self.marks(third), [Mark("run", a, count=3)])

    def test_pesos_and_chips_are_kept_apart(self):
        self.club.session(self.days[0], {"A": (1000, 1500), "B": (1000, 500)})
        self.club.session(self.days[1], {"A": (1000, 1500), "B": (1000, 500)}, unit="chips")
        third = self.club.session(self.days[2], {"A": (1000, 1100), "B": (1000, 900)})
        self.assertEqual(self.marks(third), [])
        self.assertEqual(self.marks(third, unit="chips"), [])

    def test_an_archived_session_does_not_count(self):
        first = self.club.session(self.days[0], {"A": (1000, 1500), "B": (1000, 500)})
        self.club.session(self.days[1], {"A": (1000, 1500), "B": (1000, 500)})
        third = self.club.session(self.days[2], {"A": (1000, 1100), "B": (1000, 900)})
        games.archive_night(first.night_id, self.club.host)
        self.assertEqual(self.marks(third), [])

    def test_a_session_still_open_has_no_marks(self):
        for day in self.days[:2]:
            self.club.session(day, {"A": (1000, 1500), "B": (1000, 500)})
        third = self.club.session(self.days[2], {"A": (1000, 1100), "B": (1000, 900)}, close=False)
        self.assertEqual(self.marks(third), [])
