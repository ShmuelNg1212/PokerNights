import uuid
from unittest import mock

from django.contrib import admin
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from games import services as games
from games.tests.helpers import STAKES
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_user
from ledger import services as ledger
from ledger.models import BuyIn, CashOut, Finalization, PlayerResult
from ledger.tests.helpers import Night
from ledger.tests.test_balance import override, worked_example
from settlement import queries, services
from settlement.models import SettlementPlan, Transfer


def names(transfers):
    return [(t.payer.member.display_name, t.payee.member.display_name, t.amount) for t in transfers]


class FinalizeTests(TestCase):
    def test_worked_example_end_to_end(self):
        night = worked_example()
        finalization = services.finalize(night.session.pk, night.host)
        outcome = queries.outcome(night.session)
        self.assertEqual(
            [(r.participant.member.display_name, r.buy_in_total, r.cash_out, r.net) for r in outcome.results],
            [("A", 100000, 160000, 60000), ("B", 100000, 70000, -30000), ("C", 50000, 20000, -30000)],
        )
        self.assertEqual(names(outcome.transfers), [("B", "A", 30000), ("C", "A", 30000)])
        self.assertEqual((finalization.total_buy_in, finalization.total_cash_out), (250000, 250000))
        self.assertEqual((finalization.revision, finalization.is_current), (1, True))
        self.assertEqual(sum(r.net for r in outcome.results), 0)
        self.assertTrue(finalization.plan.proven_minimal)
        session = night.refresh()
        self.assertEqual(session.state, "finalized")
        self.assertIsNotNone(session.finalized_at)

    def test_results_copy_what_statistics_need(self):
        night = worked_example()
        services.finalize(night.session.pk, night.host)
        result = PlayerResult.objects.get(participant=night.players["A"])
        self.assertEqual((result.member_id, result.group_id, result.game_date), (night.players["A"].member_id, night.group.pk, night.session.game_date))
        self.assertEqual((result.buy_in_count, result.cashed_out, result.unit), (1, 160000, "php"))

    def test_unbalanced_session_is_refused(self):
        night = worked_example((1600, 700, 250))
        with self.assertRaisesMessage(RuleError, "₱50 too much"):
            services.finalize(night.session.pk, night.host)
        missing = worked_example((1600, 900, None))
        with self.assertRaisesMessage(RuleError, "No cash-out is recorded for: C"):
            services.finalize(missing.session.pk, missing.host)
        self.assertEqual(Finalization.objects.count(), 0)
        self.assertEqual(night.refresh().state, "reconciliation")

    def test_override_lets_it_finalize_and_results_still_sum_to_zero(self):
        night = worked_example((1600, 700, 250))
        override(night, name="A", note="overpaid")
        services.finalize(night.session.pk, night.host)
        outcome = queries.outcome(night.session)
        a, b, c = outcome.results
        self.assertEqual((a.cashed_out, a.adjustment, a.cash_out, a.net), (160000, -5000, 155000, 55000))
        self.assertEqual((b.net, c.net), (-30000, -25000))
        self.assertEqual(sum(r.net for r in outcome.results), 0)
        self.assertEqual(outcome.finalization.raw_difference, 5000)
        self.assertEqual(names(outcome.transfers), [("B", "A", 30000), ("C", "A", 25000)])

    def test_centavo_amounts_stay_exact(self):
        night = worked_example((1600, 700, None))
        ledger.record_cash_out(night.session.pk, night.host, night.players["A"].pk, 1, uuid.uuid4())  # ₱0.01
        ledger.record_cash_out(night.session.pk, night.host, night.players["C"].pk, 19999, uuid.uuid4())  # ₱199.99
        services.finalize(night.session.pk, night.host)
        outcome = queries.outcome(night.session)
        self.assertEqual([r.net for r in outcome.results], [60001, -30000, -30001])
        self.assertEqual(sum(r.net for r in outcome.results), 0)
        self.assertEqual(sum(t.amount for t in outcome.transfers), 60001)

    def test_several_rebuys_and_stepwise_cash_outs(self):
        night = Night("A", "B", "C", "D")
        for name, pesos in [("A", 1000), ("B", 1000), ("C", 500), ("D", 2000), ("B", 1000), ("B", 500), ("C", 500)]:
            night.buy(name, pesos)
        night.cash("D", 500)
        night.cash("D", 1200, left=True)
        night.go("reconciliation")
        night.cash("A", 3000)
        night.cash("B", 0)
        night.cash("C", 1800)
        services.finalize(night.session.pk, night.host)
        outcome = queries.outcome(night.session)
        self.assertEqual([r.net for r in outcome.results], [200000, -250000, 80000, -30000])
        self.assertEqual([r.buy_in_count for r in outcome.results], [1, 3, 2, 1])
        self.assertEqual(len(outcome.transfers), 3)
        self.assertEqual(sum(t.amount for t in outcome.transfers), 280000)

    def test_break_even_night_has_no_transfers(self):
        night = worked_example((1000, 1000, 500))
        services.finalize(night.session.pk, night.host)
        outcome = queries.outcome(night.session)
        self.assertEqual([r.net for r in outcome.results], [0, 0, 0])
        self.assertEqual(outcome.transfers, [])

    def test_player_without_a_buy_in_gets_no_result(self):
        night = worked_example()
        games.transition(night.session.pk, night.host, "resume")
        night.add_login_player("watcher")
        games.transition(night.session.pk, night.host, "end")
        services.finalize(night.session.pk, night.host)
        self.assertEqual(PlayerResult.objects.count(), 3)

    def test_only_a_host_finalizes_and_only_after_play_ends(self):
        night = worked_example()
        player = add_player(night.group, "ben")
        with self.assertRaises(NotAllowed):
            services.finalize(night.session.pk, player)
        running = Night("X")
        running.buy("X", 1000)
        running.cash("X", 1000)
        with self.assertRaises(RuleError):
            services.finalize(running.session.pk, running.host)

    def test_second_finalize_changes_nothing(self):
        night = worked_example()
        first = services.finalize(night.session.pk, night.host)
        again = services.finalize(night.session.pk, night.host)
        self.assertEqual(first.pk, again.pk)
        self.assertEqual((Finalization.objects.count(), SettlementPlan.objects.count(), Transfer.objects.count()), (1, 1, 2))

    def test_failure_inside_the_transaction_leaves_nothing_behind(self):
        night = worked_example()
        version = night.refresh().version
        with mock.patch("settlement.services.algorithm.settle", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                services.finalize(night.session.pk, night.host)
        self.assertEqual((Finalization.objects.count(), PlayerResult.objects.count(), SettlementPlan.objects.count()), (0, 0, 0))
        session = night.refresh()
        self.assertEqual((session.state, session.version), ("reconciliation", version))

    def test_transfers_that_do_not_clear_the_balances_abort(self):
        night = worked_example()
        a, b = night.players["A"].pk, night.players["B"].pk
        with mock.patch("settlement.services.algorithm.settle", return_value=[(b, a, 30000)]):
            with self.assertRaises(ledger.LedgerInvariantError):
                services.finalize(night.session.pk, night.host)
        self.assertEqual((Finalization.objects.count(), Transfer.objects.count()), (0, 0))

    def test_database_refuses_results_that_break_conservation(self):
        night = worked_example()
        finalization = services.finalize(night.session.pk, night.host)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Finalization.objects.filter(pk=finalization.pk).update(total_cash_out=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PlayerResult.objects.filter(finalization=finalization).update(net=1)


class AfterFinalizationTests(TestCase):
    def setUp(self):
        self.night = worked_example()
        services.finalize(self.night.session.pk, self.night.host)
        self.session, self.host = self.night.session, self.night.host

    def test_every_money_write_is_refused(self):
        a = self.night.players["A"]
        buy_in = BuyIn.objects.filter(participant=a).first()
        cash_out = CashOut.objects.filter(participant=a).first()
        attempts = [
            lambda: ledger.record_buy_in(self.session.pk, self.host, a.pk, 100000, uuid.uuid4()),
            lambda: ledger.reverse_buy_in(self.session.pk, self.host, buy_in.pk, "late"),
            lambda: ledger.record_cash_out(self.session.pk, self.host, a.pk, 5, uuid.uuid4()),
            lambda: ledger.reverse_cash_out(self.session.pk, self.host, cash_out.pk, "late"),
            lambda: ledger.record_override(self.session.pk, self.host, "note", "equal", None, uuid.uuid4()),
            lambda: ledger.void_override(self.session.pk, self.host),
            lambda: games.update_settings(self.session.pk, self.host, {**STAKES, "big_blind": 4000}),
            lambda: games.add_participant(self.session.pk, self.host, self.host.pk),
            lambda: games.set_left(self.session.pk, self.host, a.pk),
            lambda: games.transition(self.session.pk, self.host, "resume"),
            lambda: games.transition(self.session.pk, self.host, "cancel", "oops"),
        ]
        for attempt in attempts:
            with self.assertRaises(RuleError):
                attempt()
        outcome = queries.outcome(self.session)
        self.assertEqual([r.net for r in outcome.results], [60000, -30000, -30000])
        self.assertEqual((BuyIn.objects.count(), CashOut.objects.count()), (3, 3))

    def test_later_preset_or_table_changes_do_not_touch_the_snapshot(self):
        finalization = Finalization.objects.get()
        self.assertEqual(finalization.settings_snapshot[0]["default_buy_in"], 100000)
        self.assertEqual(finalization.unit, "php")
        self.assertNotIn("chips_per_buy_in", finalization.settings_snapshot[0])

    def test_money_rows_are_read_only_in_the_admin(self):
        for model in (BuyIn, CashOut, Finalization, PlayerResult, SettlementPlan, Transfer):
            model_admin = admin.site._registry[model]
            self.assertFalse(model_admin.has_change_permission(None), model)
            self.assertFalse(model_admin.has_delete_permission(None), model)
            self.assertFalse(model_admin.has_add_permission(None), model)


class FinalizeViewTests(TestCase):
    def test_host_finalizes_and_everyone_sees_results_and_transfers(self):
        night = worked_example()
        ben = add_player(night.group, "ben")
        self.client.force_login(night.host.user)
        page = self.client.get(reverse("session", args=[night.session.pk]))
        self.assertContains(page, "The books balance")
        self.assertContains(page, "Finalize results")
        page = self.client.post(reverse("session_finalize", args=[night.session.pk]), follow=True)
        for text in ("+₱600", "−₱300", "<strong>B</strong> pays <strong>A</strong>", "<strong>C</strong> pays <strong>A</strong>", "₱2,500"):
            self.assertContains(page, text)
        for gone in ("buyins/add", "cashouts/add", "Finalize results", "override/", "Host controls", "Still in play", "seats free", "chips"):
            self.assertNotContains(page, gone)
        self.client.force_login(ben.user)
        page = self.client.get(reverse("session", args=[night.session.pk]))
        self.assertContains(page, "<strong>B</strong> pays <strong>A</strong>")

    def test_player_sees_own_result_and_what_they_owe(self):
        night = Night("A", "C")
        ben = night.add_login_player("ben")
        night.buy("A", 1000)
        night.buy("ben", 1000)
        night.buy("C", 500)
        night.go("reconciliation")
        night.cash("A", 1600)
        night.cash("ben", 700)
        night.cash("C", 200)
        services.finalize(night.session.pk, night.host)
        self.client.force_login(ben.user)
        page = self.client.get(reverse("session", args=[night.session.pk]))
        self.assertContains(page, "Your result")
        self.assertContains(page, "You pay <strong>A</strong>")
        self.assertContains(page, "Bought in ₱1,000 · cashed out ₱700")

    def test_unbalanced_finalize_shows_the_reason(self):
        night = worked_example((1600, 700, 150))
        self.client.force_login(night.host.user)
        page = self.client.get(reverse("session", args=[night.session.pk]))
        self.assertNotContains(page, "Finalize results")
        page = self.client.post(reverse("session_finalize", args=[night.session.pk]), follow=True)
        self.assertContains(page, "₱50 is missing")
        self.assertEqual(night.refresh().state, "reconciliation")

    def test_player_and_stranger_cannot_finalize(self):
        night = worked_example()
        ben = add_player(night.group, "ben")
        url = reverse("session_finalize", args=[night.session.pk])
        self.client.force_login(ben.user)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertEqual(Finalization.objects.count(), 0)
