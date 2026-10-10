"""The closing recap reads frozen results: who, how much, in which set, and for how long."""
from django.test import TestCase

from games import services as games
from games.models import GameNight
from ledger.models import PlayerResult
from ledger.tests.helpers import Night
from settlement import queries, services
from settlement.tests.test_night import TwoSets


def recap_of(night_id, viewer_id=None, seconds=None):
    night = GameNight.objects.get(pk=night_id)
    outcome = queries.night_outcome(night)
    return queries.night_recap(night, outcome.standings, seconds or {}, results=outcome.results, viewer_id=viewer_id)


def names(standings):
    return [s.member.display_name for s in standings]


class RecapFactsTests(TestCase):
    """TwoSets. Set 1: A +600, B −300, C −300. Set 2: A −400, B +400, C even."""

    def setUp(self):
        self.two = TwoSets()
        services.close_night(self.two.night_id, self.two.host)

    def test_glance_counts_players_sets_and_buy_ins(self):
        recap = recap_of(self.two.night_id)
        self.assertEqual((recap.players, recap.set_count, recap.buy_ins), (3, 2, 6))
        self.assertEqual(recap.total_buy_in, 500000)
        self.assertEqual(names(recap.winners), ["A"])

    def test_ranking_lists_everyone_with_their_frozen_figures(self):
        recap = recap_of(self.two.night_id)
        self.assertEqual(
            [(line.place, line.member.display_name, line.buy_in, line.cash_out, line.buy_ins, line.net)
             for line in recap.ranking],
            [(1, "A", 200000, 220000, 2, 20000), (2, "B", 200000, 210000, 2, 10000), (3, "C", 100000, 70000, 2, -30000)],
        )
        self.assertEqual([line.share for line in recap.ranking], [66, 33, 100])
        self.assertEqual(recap.ranking[0].sets, [(1, 60000), (2, -40000)])

    def test_tied_results_share_a_place(self):
        night = Night("A", "B", "C")
        for name, cash in (("A", 1500), ("B", 1500), ("C", 0)):
            night.buy(name, 1000)
        night.go("reconciliation")
        for name, cash in (("A", 1500), ("B", 1500), ("C", 0)):
            night.cash(name, cash)
        services.finalize(night.session.pk, night.host)
        recap = recap_of(night.session.night_id)
        self.assertEqual([(line.place, line.member.display_name) for line in recap.ranking], [(1, "A"), (1, "B"), (3, "C")])

    def test_sets_have_their_own_pot_players_and_top_result(self):
        recap = recap_of(self.two.night_id, seconds={self.two.first.pk: 3600})
        first, second = recap.sets
        self.assertEqual((first.number, first.players, first.total_buy_in, first.seconds), (1, 3, 250000, 3600))
        self.assertEqual([(s.member.display_name, net) for s, net in first.winners], [("A", 60000)])
        self.assertEqual((second.number, second.seconds), (2, None))
        self.assertEqual([(s.member.display_name, net) for s, net in second.winners], [("B", 40000)])

    def test_viewer_gets_their_own_line_and_a_non_player_gets_none(self):
        member = self.two.night.players["B"].member
        self.assertEqual(recap_of(self.two.night_id, viewer_id=member.pk).mine.net, 10000)
        self.assertIsNone(recap_of(self.two.night_id, viewer_id=self.two.host.pk).mine)

    def test_a_canceled_set_is_counted_nowhere(self):
        two = TwoSets(finalize_second=False)
        games.transition(two.second.pk, two.host, "cancel", "Synthetic cancellation")
        recap = recap_of(two.night_id)
        self.assertEqual((recap.set_count, recap.buy_ins, [s.number for s in recap.sets]), (1, 3, [1]))
        self.assertEqual([line.sets for line in recap.ranking], [[(1, 60000)], [(1, -30000)], [(1, -30000)]])

    def test_superseded_results_are_not_read(self):
        stale = PlayerResult.objects.filter(finalization__session=self.two.first).first()
        before = recap_of(self.two.night_id)
        PlayerResult.objects.filter(pk=stale.pk).update(is_current=False)
        after = recap_of(self.two.night_id)
        self.assertEqual(before.buy_ins - after.buy_ins, stale.buy_in_count)

    def test_reading_the_recap_from_loaded_results_costs_one_query(self):
        night = GameNight.objects.get(pk=self.two.night_id)
        outcome = queries.night_outcome(night)
        with self.assertNumQueries(1):  # the sets' frozen totals
            queries.night_recap(night, outcome.standings, {}, results=outcome.results)


class RecapHighlightTests(TestCase):
    def setUp(self):
        self.two = TwoSets()

    def highlights(self, **kwargs):
        return {h.kind: h for h in recap_of(self.two.night_id, **kwargs).highlights}

    def test_biggest_single_set_win_names_the_player_and_the_set(self):
        found = self.highlights()["set_win"]
        self.assertEqual([(s.member.display_name, number) for s, number in found.entries], [("A", 1)])
        self.assertEqual(found.amount, 60000)

    def test_equal_buy_in_counts_say_nothing(self):
        self.assertNotIn("buy_ins", self.highlights())

    def test_most_buy_ins_names_every_tie(self):
        rows = PlayerResult.objects.filter(is_current=True, finalization__session=self.two.first)
        rows.exclude(member=self.two.night.players["C"].member).update(buy_in_count=3)
        found = self.highlights()["buy_ins"]
        self.assertEqual(([s.member.display_name for s, _ in found.entries], found.count), (["A", "B"], 4))

    def test_longest_at_the_table_needs_two_recorded_unequal_times(self):
        rows = PlayerResult.objects.filter(is_current=True, finalization__session__night_id=self.two.night_id)
        of = lambda name: rows.filter(member=self.two.night.players[name].member, finalization__session=self.two.first)
        rows.update(play_seconds=None)  # as in sets played before playing time was recorded
        self.assertNotIn("longest", self.highlights())
        of("A").update(play_seconds=600)
        self.assertNotIn("longest", self.highlights())  # one known time
        of("B").update(play_seconds=600)
        self.assertNotIn("longest", self.highlights())  # all equal
        of("B").update(play_seconds=900)
        found = self.highlights()["longest"]
        self.assertEqual(([s.member.display_name for s, _ in found.entries], found.seconds), (["B"], 900))

    def test_no_highlight_names_a_loss(self):
        for found in self.highlights().values():
            self.assertFalse(found.amount is not None and found.amount <= 0)
        self.assertEqual(set(self.highlights()) - {"buy_ins", "set_win", "longest"}, set())

    def test_one_set_has_no_single_set_highlight(self):
        two = TwoSets(finalize_second=False)
        games.transition(two.second.pk, two.host, "cancel", "Synthetic cancellation")
        self.assertEqual(recap_of(two.night_id).highlights, [])
