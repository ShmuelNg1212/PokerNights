"""The stats engine works every figure out from one list of frozen results, with integers only."""

import datetime
from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase

from groups import services as groups
from ledger.models import PlayerResult
from settlement import queries, services, stats
from settlement.stats import Period, PlayerRecord, SessionResult

from .test_stats import OCT_1, SEP_30, Club

D = datetime.date


def night(member, day, net, *, bought=1000, rebuys=0, rake=0, seconds=None, night_id=None):
    return SessionResult(member, night_id or day.toordinal(), day, "Main table", net, bought, rebuys, rake, seconds)


def record(*nets, **kwargs):
    days = [D(2026, 1, 1) + datetime.timedelta(days=7 * n) for n in range(len(nets))]
    return PlayerRecord(SimpleNamespace(pk=1, display_name="Ana"), [night(1, day, net, **kwargs) for day, net in zip(days, nets)])


class FigureTests(SimpleTestCase):
    def test_totals_wins_and_running(self):
        r = record(500, -200, 0, 300)
        self.assertEqual((r.net, r.sessions, r.wins, r.win_percent), (600, 4, 2, 50))
        self.assertEqual(r.running, [500, 300, 300, 600])
        self.assertEqual((r.best.net, r.worst.net, r.last.net), (500, -200, 300))

    def test_division_rounds_toward_zero_so_a_loss_is_never_overstated(self):
        self.assertEqual(record(-100, -200, -200).average, -166)   # −166.67
        self.assertEqual(record(100, 200, 200).average, 166)
        self.assertEqual(record(-1, 0, 0, bought=300).return_percent, 0)   # −0.11%
        self.assertEqual(record(-500, bought=1500).return_percent, -33)
        self.assertEqual(record(500, bought=1500).return_percent, 33)
        self.assertIsNone(record(0, bought=0).return_percent)

    def test_per_hour_uses_only_sessions_with_time(self):
        r = PlayerRecord(None, [
            night(1, D(2026, 1, 1), 900, seconds=3 * 3600), night(1, D(2026, 1, 8), -300, seconds=1800),
            night(1, D(2026, 1, 15), 5000), night(1, D(2026, 1, 22), 100, seconds=0),
        ])
        self.assertEqual((r.timed_sessions, r.seconds), (2, 3 * 3600 + 1800))
        self.assertEqual(r.per_hour, 171)   # 600 over 3.5 hours = 171.43
        self.assertIsNone(record(100, 200).per_hour)

    def test_rebuys_rake_and_bought_in(self):
        r = record(100, 100, 100, bought=2000, rebuys=1, rake=50)
        self.assertEqual((r.bought_in, r.rake, r.rebuys, r.rebuys_per_session), (6000, 150, 3, "1.0"))
        self.assertEqual(PlayerRecord(None, [night(1, D(2026, 1, 1), 0, rebuys=4), night(1, D(2026, 1, 2), 0), night(1, D(2026, 1, 3), 0)]).rebuys_per_session, "1.3")

    def test_runs(self):
        self.assertEqual(record(100, -50, 200, 300, 100).current_run, ("won", 3))
        self.assertEqual(record(100, -50, -20).current_run, ("lost", 2))
        self.assertIsNone(record(100, 0).current_run)        # a break-even night ends a run
        self.assertIsNone(record().current_run)
        self.assertEqual(record(100, 100, 0, 100, 100, 100, -1, 100).longest_win_run, 3)
        self.assertEqual(record(-1, -1).longest_win_run, 0)

    def test_best_and_worst_take_the_earliest_on_a_tie(self):
        r = record(300, -100, 300, -100)
        self.assertEqual((r.best.date, r.worst.date), (D(2026, 1, 1), D(2026, 1, 8)))


class PeriodTests(SimpleTestCase):
    TODAY = D(2026, 10, 9)

    def test_bounds(self):
        year, recent, month = Period.parse("year", self.TODAY), Period.parse("recent", self.TODAY), Period.parse("2026-02", self.TODAY)
        self.assertEqual((year.start, year.end), (D(2026, 1, 1), D(2026, 12, 31)))
        self.assertEqual((recent.start, recent.end), (D(2026, 8, 1), D(2026, 10, 31)))
        self.assertEqual((month.start, month.end), (D(2026, 2, 1), D(2026, 2, 28)))
        self.assertTrue(recent.contains(D(2026, 8, 1)) and not recent.contains(D(2026, 7, 31)))
        self.assertTrue(Period.parse("all", self.TODAY).contains(D(1999, 1, 1)))
        self.assertEqual(Period.parse("recent", D(2026, 1, 15)).start, D(2025, 11, 1))

    def test_unknown_values_fall_back_to_all_time(self):
        for bad in ("", None, "2026-13", "nope", "20261"):
            self.assertEqual(Period.parse(bad, self.TODAY).slug, "all")

    def test_minimums_labels_and_slugs(self):
        found = {slug: Period.parse(slug, self.TODAY) for slug in ("all", "year", "recent", "2026-09")}
        self.assertEqual({k: p.minimum for k, p in found.items()}, {"all": 3, "year": 3, "recent": 2, "2026-09": 1})
        self.assertEqual({k: p.label for k, p in found.items()}, {"all": "All time", "year": "This year", "recent": "Last 3 months", "2026-09": "September 2026"})
        self.assertEqual({k: p.slug for k, p in found.items()}, {k: k for k in found})

    def test_previous(self):
        rows = [night(1, D(2026, 9, 1), 0), night(1, D(2026, 10, 2), 0), night(2, D(2026, 10, 2), 0)]
        p = lambda slug: Period.parse(slug, self.TODAY).previous(rows)
        self.assertEqual((p("year").start, p("year").end), (D(2025, 1, 1), D(2025, 12, 31)))
        self.assertEqual((p("recent").start, p("recent").end), (D(2026, 5, 1), D(2026, 7, 31)))
        self.assertEqual((p("2026-01").start, p("2026-01").end), (D(2025, 12, 1), D(2025, 12, 31)))
        self.assertEqual((p("all").start, p("all").end), (None, D(2026, 10, 1)))   # before the latest session
        self.assertIsNone(Period.parse("all", self.TODAY).previous([]))


def people(*names):
    return {n: SimpleNamespace(pk=n, display_name=name) for n, name in enumerate(names, 1)}


class BoardTests(SimpleTestCase):
    TODAY = D(2026, 10, 9)

    def rows(self, spec):
        """``spec`` is ``{member id: [net, ...]}``; one night a week from August, the same nights for everyone."""
        days = [D(2026, 8, 1) + datetime.timedelta(days=7 * n) for n in range(12)]
        return [night(m, day, net, seconds=3600) for m, nets in spec.items() for day, net in zip(days, nets)]

    def board(self, spec, sort="profit", period="all", names=("Ana", "Ben", "Carlo", "Dani")):
        return stats.board(self.rows(spec), people(*names), Period.parse(period, self.TODAY), sort)

    def test_minimum_splits_ranked_from_not_ranked(self):
        board = self.board({1: [100, 100, 100], 2: [900, 900], 3: [-50, -50, -50], 4: [5000]})
        self.assertEqual([(l.place, l.record.member.display_name) for l in board.ranked], [(1, "Ana"), (2, "Carlo")])
        self.assertEqual([l.record.member.display_name for l in board.unranked], ["Dani", "Ben"])   # by profit, no place
        self.assertTrue(all(l.place is None for l in board.unranked))
        self.assertEqual(board.minimum, 3)

    def test_each_sort_and_its_ties(self):
        spec = {1: [300, 300, 300], 2: [100, 100, 100, 100, 100, 100, 100, 100, 100, 100], 3: [300, 300, 300]}
        order = lambda sort: [l.record.member.display_name for l in self.board(spec, sort).ranked]
        self.assertEqual(order("profit"), ["Ben", "Ana", "Carlo"])       # 1000, then 900 and 900 by name
        self.assertEqual(order("average"), ["Ana", "Carlo", "Ben"])
        self.assertEqual(order("return"), ["Ana", "Carlo", "Ben"])
        self.assertEqual(order("hour"), ["Ana", "Carlo", "Ben"])
        self.assertEqual(order("sessions"), ["Ben", "Ana", "Carlo"])
        self.assertEqual(order("nonsense"), order("profit"))

    def test_per_hour_sort_needs_time_and_is_offered_only_then(self):
        rows = [night(1, D(2026, 8, n), 100) for n in (1, 2, 3)]
        board = stats.board(rows, people("Ana"), Period.parse("all", self.TODAY), "hour")
        self.assertFalse(board.has_time)
        self.assertEqual(board.sort, "profit")

    def test_movement_against_the_board_before_the_latest_session(self):
        # Before the last night: Ana 300, Ben 200, Carlo 100 (three nights each). The last night lifts Carlo and adds Dani.
        spec = {1: [100, 100, 100, 0], 2: [100, 50, 50, 0], 3: [50, 25, 25, 900], 4: [None, 400, 400, 400]}
        days = [D(2026, 9, 1), D(2026, 9, 8), D(2026, 9, 15), D(2026, 9, 22)]
        rows = [night(m, day, net) for m, nets in spec.items() for day, net in zip(days, nets) if net is not None]
        board = stats.board(rows, people("Ana", "Ben", "Carlo", "Dani"), Period.parse("all", self.TODAY), "profit")
        moves = {l.record.member.display_name: l.move for l in board.ranked}
        self.assertEqual(moves, {"Dani": "new", "Carlo": 1, "Ana": -2, "Ben": -2})

    def test_no_marks_when_there_is_no_earlier_board(self):
        board = self.board({1: [100, 100, 100], 2: [50, 50, 50]}, period="2026-08")
        self.assertEqual([l.move for l in board.ranked], [None, None])

    def test_a_period_takes_only_its_sessions(self):
        board = self.board({1: [100] * 12}, period="2026-09")
        self.assertEqual(board.ranked[0].record.sessions, 4)

    def test_place_of_one_member(self):
        board = self.board({1: [100, 100, 100], 2: [900, 900, 900], 3: [5]})
        self.assertEqual((board.line(1).place, board.line(3).place, board.line(99)), (2, None, None))
        self.assertEqual(board.ranked_count, 2)


class FetchTests(TestCase):
    def test_one_row_per_player_and_session_and_agreement_with_the_old_board(self):
        club = Club()
        club.session(SEP_30, {"A": (1000, 1200), "B": (1000, 800)})
        club.session(OCT_1, {"A": (500, 400), "C": (500, 600)}, unit="chips")
        club.session(OCT_1, {"B": (1000, 1000), "D": (1000, 1000)}, close=False)
        club.session(OCT_1, {"A": (1000, 1000)}, cancel=True)
        rows = stats.fetch(club.group, "php")
        self.assertEqual([(club_name(club, r.member_id), r.date, r.net, r.bought_in, r.rebuys, r.table) for r in rows],
                         [("A", SEP_30, 20000, 100000, 0, "Friday table"), ("B", SEP_30, -20000, 100000, 0, "Friday table")])
        self.assertEqual([r.net for r in stats.fetch(club.group, "chips")], [-100, 100])
        board = stats.board(rows, stats.members_of(rows), Period.parse("2026-09", OCT_1), "profit")
        old = {s.member.display_name: (s.net, s.sessions, s.wins) for s in queries.group_stats(club.group, "php", SEP_30)}
        self.assertEqual({l.record.member.display_name: (l.record.net, l.record.sessions, l.record.wins) for l in board.ranked}, old)

    def test_rebuys_time_and_a_removed_player(self):
        club = Club()
        one = club.session(OCT_1, {"A": (1000, 1500), "B": (1000, 500)})
        PlayerResult.objects.filter(finalization__session=one, member=club.member("A")).update(buy_in_count=3, play_seconds=7200, rake_total=500)
        groups.remove_member(club.host, club.member("B").pk)
        a, b = stats.fetch(club.group, "php")
        self.assertEqual((a.rebuys, a.seconds, a.rake), (2, 7200, 500))
        self.assertEqual(stats.members_of([a, b])[b.member_id].status, "removed")

    def test_two_queries_however_many_players_and_sessions(self):
        club = Club()
        for day in (SEP_30, OCT_1):
            club.session(day, {name: (1000, 1000) for name in "ABCDEFGH"})
        with self.assertNumQueries(2):
            rows = stats.fetch(club.group, "php")
            stats.board(rows, stats.members_of(rows), Period.parse("all", OCT_1), "profit")


def club_name(club, member_id):
    return next(name for name, member in club.members.items() if member.pk == member_id)
