"""Settle-up happens once per session, over all of its sets."""

import uuid
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from games import services as games
from games.models import GameNight, Participant
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_user
from ledger import services as ledger
from ledger.models import PlayerResult
from ledger.tests.helpers import Night
from settlement import queries, services
from settlement.models import Payment, SettlementPlan, Transfer

from .test_finalize import names


class TwoSets:
    """A session with two sets. Set 1: A +600, B −300, C −300. Set 2: B wins ₱400 from A; C breaks even."""

    def __init__(self, finalize_second=True):
        self.night = night = Night("A", "B", "C")
        self.host = night.host
        self.first = night.session
        self.play(self.first, night.players, {"A": (1000, 1600), "B": (1000, 700), "C": (500, 200)})
        services.finalize(self.first.pk, self.host)
        self.second = games.start_next_set(self.first.night_id, self.host)
        self.players2 = {p.member.display_name: p for p in Participant.objects.filter(session=self.second)}
        games.transition(self.second.pk, self.host, "start", opening_buy_ins=False)
        if finalize_second:
            self.finish_second()

    def play(self, game, players, figures, end=True):
        for name, (buy_in, _) in figures.items():
            ledger.record_buy_in(game.pk, self.host, players[name].pk, buy_in * 100, uuid.uuid4())
        game.refresh_from_db()
        if end and game.state == "running":
            games.transition(game.pk, self.host, "end")
        for name, (_, cash_out) in figures.items():
            ledger.record_cash_out(game.pk, self.host, players[name].pk, cash_out * 100, uuid.uuid4())

    def finish_second(self):
        self.play(self.second, self.players2, {"A": (1000, 600), "B": (1000, 1400), "C": (500, 500)})
        services.finalize(self.second.pk, self.host)

    @property
    def night_id(self):
        return self.first.night_id


class CloseNightTests(TestCase):
    def test_transfers_net_both_sets(self):
        two = TwoSets()
        self.assertEqual((SettlementPlan.objects.count(), Transfer.objects.count()), (0, 0))
        plan = services.close_night(two.night_id, two.host)
        outcome = queries.night_outcome(GameNight.objects.get(pk=two.night_id))
        self.assertEqual(
            [(s.member.display_name, s.net, s.sets_played) for s in outcome.standings],
            [("A", 20000, 2), ("B", 10000, 2), ("C", -30000, 2)],
        )
        self.assertEqual(names(outcome.transfers), [("C", "A", 20000), ("C", "B", 10000)])
        self.assertEqual(sum(s.net for s in outcome.standings), 0)
        self.assertTrue(plan.proven_minimal)
        night = GameNight.objects.get(pk=two.night_id)
        self.assertEqual(night.status, "closed")
        self.assertIsNotNone(night.closed_at)
        # Set results are untouched by the close.
        self.assertEqual(sorted(PlayerResult.objects.values_list("net", flat=True)), [-40000, -30000, -30000, 0, 40000, 60000])

    def test_refused_while_a_set_is_not_finalized_and_names_it(self):
        two = TwoSets(finalize_second=False)
        with self.assertRaisesMessage(RuleError, "Not done: set 2 (running)"):
            services.close_night(two.night_id, two.host)
        games.transition(two.second.pk, two.host, "end")
        with self.assertRaisesMessage(RuleError, "Not done: set 2 (counting up)"):
            services.close_night(two.night_id, two.host)
        self.assertEqual((SettlementPlan.objects.count(), GameNight.objects.get(pk=two.night_id).status), (0, "open"))

    def test_a_canceled_set_counts_for_nothing(self):
        two = TwoSets(finalize_second=False)
        games.transition(two.second.pk, two.host, "cancel", "everyone went home")
        services.close_night(two.night_id, two.host)
        outcome = queries.night_outcome(GameNight.objects.get(pk=two.night_id))
        self.assertEqual(names(outcome.transfers), [("B", "A", 30000), ("C", "A", 30000)])
        self.assertEqual([s.sets_played for s in outcome.standings], [1, 1, 1])

    def test_session_with_only_canceled_sets_has_nothing_to_settle(self):
        night = Night("A", state="open")
        games.transition(night.session.pk, night.host, "cancel", "rain")
        with self.assertRaisesMessage(RuleError, "nothing to settle"):
            services.close_night(night.session.night_id, night.host)

    def test_a_player_who_joined_only_the_second_set_is_included(self):
        two = TwoSets(finalize_second=False)
        from groups import services as groups
        dee = games.add_participant(two.second.pk, two.host, groups.add_roster_player(two.host, "Dee").pk)
        two.players2["Dee"] = dee
        two.play(two.second, two.players2, {"A": (1000, 600), "B": (1000, 1400), "C": (500, 500), "Dee": (500, 500)})
        services.finalize(two.second.pk, two.host)
        services.close_night(two.night_id, two.host)
        outcome = queries.night_outcome(GameNight.objects.get(pk=two.night_id))
        self.assertEqual([(s.member.display_name, s.net, s.sets_played) for s in outcome.standings][-1], ("Dee", 0, 1))
        self.assertEqual(len(outcome.transfers), 2)  # a break-even player is in no transfer

    def test_closing_twice_changes_nothing_and_a_closed_session_gets_no_new_set(self):
        two = TwoSets()
        first = services.close_night(two.night_id, two.host)
        again = services.close_night(two.night_id, two.host)
        self.assertEqual(first.pk, again.pk)
        self.assertEqual((SettlementPlan.objects.count(), Transfer.objects.count()), (1, 2))
        with self.assertRaisesMessage(RuleError, "closed"):
            games.start_next_set(two.night_id, two.host)

    def test_failure_inside_the_close_leaves_nothing_behind(self):
        two = TwoSets()
        a, b = two.night.players["A"].member_id, two.night.players["B"].member_id
        with mock.patch("settlement.services.algorithm.settle", return_value=[(b, a, 30000)]):
            with self.assertRaises(ledger.LedgerInvariantError):
                services.close_night(two.night_id, two.host)
        with mock.patch("settlement.services.algorithm.settle", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                services.close_night(two.night_id, two.host)
        self.assertEqual((SettlementPlan.objects.count(), Transfer.objects.count()), (0, 0))
        self.assertEqual(GameNight.objects.get(pk=two.night_id).status, "open")

    def test_only_a_host_of_the_group_closes(self):
        two = TwoSets()
        with self.assertRaises(NotAllowed):
            services.close_night(two.night_id, add_player(two.night.group, "ben"))
        from groups.tests.helpers import make_group
        _, other_host = make_group("omar", "Other")
        with self.assertRaises(RuleError):
            services.close_night(two.night_id, other_host)

    def test_paid_marks_work_on_session_transfers(self):
        two = TwoSets()
        services.close_night(two.night_id, two.host)
        first, second = Transfer.objects.order_by("position")
        services.mark_paid(two.night_id, two.host, first.pk, uuid.uuid4())
        outcome = queries.night_outcome(GameNight.objects.get(pk=two.night_id))
        self.assertEqual((outcome.status, Payment.objects.get().night_id), ("partly", two.night_id))
        services.mark_paid(two.night_id, two.host, second.pk, uuid.uuid4())
        self.assertEqual(queries.night_outcome(GameNight.objects.get(pk=two.night_id)).status, "settled")


class NightSettlePageTests(TestCase):
    def test_session_page_shows_running_results_then_transfers(self):
        two = TwoSets(finalize_second=False)
        url = reverse("night", args=[two.night_id])
        self.client.force_login(two.host.user)
        page = self.client.get(url)
        self.assertContains(page, "Results so far")
        self.assertContains(page, "not final")
        self.assertContains(page, "Not done: set 2 (running)")
        self.assertNotContains(page, "pays <strong>")
        self.assertEqual(self.client.post(reverse("night_close", args=[two.night_id]), follow=True).status_code, 200)
        self.assertEqual(GameNight.objects.get(pk=two.night_id).status, "open")  # refused
        two.finish_second()
        page = self.client.get(url)
        self.assertContains(page, "+₱200")
        self.assertContains(page, "Close session and settle up")
        page = self.client.post(reverse("night_close", args=[two.night_id]), follow=True)
        for text in ('aria-label="C pays A"', "₱200", 'aria-label="C pays B"', "₱100", "Session results", "Unsettled", "Session closed"):
            self.assertContains(page, text)
        self.assertNotContains(page, "Start next set")
        transfer = Transfer.objects.order_by("position").first()
        page = self.client.post(reverse("transfer_paid", args=[two.night_id, transfer.pk]), follow=True)
        self.assertContains(page, "Partly settled")
        self.assertContains(page, "Payment records")
        set_page = self.client.get(reverse("session", args=[two.first.pk]))
        self.assertContains(set_page, "See who pays whom")

    def test_player_and_stranger_cannot_close_or_mark(self):
        two = TwoSets()
        ben = add_player(two.night.group, "ben")
        self.client.force_login(ben.user)
        page = self.client.get(reverse("night", args=[two.night_id]))
        self.assertNotContains(page, "Close session and settle up")
        self.assertEqual(self.client.post(reverse("night_close", args=[two.night_id])).status_code, 403)
        services.close_night(two.night_id, two.host)
        transfer = Transfer.objects.first()
        for name in ("transfer_paid", "transfer_unpaid"):
            self.assertEqual(self.client.post(reverse(name, args=[two.night_id, transfer.pk])).status_code, 403)
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.post(reverse("night_close", args=[two.night_id])).status_code, 404)
        self.assertEqual(self.client.post(reverse("transfer_paid", args=[two.night_id, transfer.pk])).status_code, 404)
        self.assertEqual(Payment.objects.count(), 0)
