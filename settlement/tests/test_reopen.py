"""Reopening a finalized set and a closed session. Nothing recorded is removed; the next finalize or close replaces it."""

import uuid

from django.test import TestCase, override_settings
from django.urls import reverse

from audit.models import AuditEvent
from games import services as games
from games.models import GameNight, GameSession
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_user
from ledger import services as ledger
from ledger.models import CashOut, Finalization, PlayerResult
from ledger.tests.helpers import Night
from settlement import queries, services
from settlement.models import Payment, SettlementPlan, Transfer

from .test_night import TwoSets


def finalized(**figures):
    """One finalized set. ``figures`` maps a name to (buy-in, cash-out) in pesos."""
    figures = figures or {"A": (1000, 1600), "B": (1000, 700), "C": (500, 200)}
    night = Night(*figures)
    for name, (buy_in, _) in figures.items():
        night.buy(name, buy_in)
    night.go("reconciliation")
    for name, (_, cash_out) in figures.items():
        night.cash(name, cash_out)
    services.finalize(night.session.pk, night.host)
    night.refresh()
    return night


def recash(night, name, pesos):
    """Correct one player's cash-out in a set that is counting up."""
    old = CashOut.objects.get(participant=night.players[name], reversal__isnull=True)
    ledger.reverse_cash_out(night.session.pk, night.host, old.pk, "miscounted")
    night.cash(name, pesos)


def nets(session):
    return {
        r.participant.member.display_name: r.net
        for r in PlayerResult.objects.filter(finalization__session=session, is_current=True)
    }


class ReopenSetTests(TestCase):
    def test_set_returns_to_counting_up_and_results_leave(self):
        night = finalized()
        before = night.session.version
        services.reopen_set(night.session.pk, night.host, "A had 100 more")
        session = night.refresh()
        self.assertEqual((session.state, session.finalized_at), ("reconciliation", None))
        self.assertIsNotNone(session.ended_at)
        self.assertGreater(session.version, before)
        retired = Finalization.objects.get(session=session)
        self.assertFalse(retired.is_current)
        self.assertEqual((retired.void_reason, retired.voided_by), ("A had 100 more", night.host.user))
        self.assertIsNotNone(retired.voided_at)
        self.assertEqual(nets(session), {})
        self.assertEqual(PlayerResult.objects.filter(finalization=retired).count(), 3)
        self.assertEqual(services.result_rows(session.night), [])

    def test_correct_and_finalize_again_writes_revision_two(self):
        night = finalized()
        services.reopen_set(night.session.pk, night.host, "A and B miscounted")
        recash(night, "A", 1500)
        recash(night, "B", 800)
        final = services.finalize(night.session.pk, night.host)
        self.assertEqual((final.revision, final.is_current), (2, True))
        self.assertEqual(nets(night.session), {"A": 50000, "B": -20000, "C": -30000})
        first = Finalization.objects.get(session=night.session, revision=1)
        self.assertEqual(sorted(r.net for r in first.results.all()), [-30000, -30000, 60000])
        self.assertFalse(first.results.filter(is_current=True).exists())
        self.assertEqual(night.refresh().state, "finalized")

    def test_reason_is_required_and_logged(self):
        night = finalized()
        with self.assertRaisesMessage(RuleError, "reason"):
            services.reopen_set(night.session.pk, night.host, "   ")
        self.assertEqual(night.refresh().state, "finalized")
        services.reopen_set(night.session.pk, night.host, "wrong count")
        event = AuditEvent.objects.get(action="session.reopened")
        self.assertEqual((event.reason, event.session_id), ("wrong count", night.session.pk))
        self.assertEqual(sorted(event.data["nets"].values()), [-30000, -30000, 60000])

    def test_a_repeated_tap_changes_nothing(self):
        night = finalized()
        services.reopen_set(night.session.pk, night.host, "wrong count")
        version = night.refresh().version
        services.reopen_set(night.session.pk, night.host, "wrong count")
        self.assertEqual(night.refresh().version, version)
        self.assertEqual(AuditEvent.objects.filter(action="session.reopened").count(), 1)

    def test_only_a_finalized_set(self):
        night = Night("A", "B")
        with self.assertRaisesMessage(RuleError, "Only a finalized set"):
            services.reopen_set(night.session.pk, night.host, "why")
        night.go("reconciliation")
        with self.assertRaisesMessage(RuleError, "Only a finalized set"):
            services.reopen_set(night.session.pk, night.host, "why")

    def test_only_a_host(self):
        night = finalized()
        player = add_player(night.group, "Player")
        with self.assertRaises(NotAllowed):
            services.reopen_set(night.session.pk, player, "why")

    def test_refused_while_the_session_is_closed(self):
        night = finalized()
        services.close_night(night.session.night_id, night.host)
        with self.assertRaisesMessage(RuleError, "Reopen the session first"):
            services.reopen_set(night.session.pk, night.host, "why")
        self.assertEqual(night.refresh().state, "finalized")

    def test_refused_in_an_archived_session(self):
        night = finalized()
        games.archive_night(night.session.night_id, night.host)
        with self.assertRaisesMessage(RuleError, "archived"):
            services.reopen_set(night.session.pk, night.host, "why")

    @override_settings(REOPENING=False)
    def test_switch_off_refuses(self):
        night = finalized()
        with self.assertRaisesMessage(RuleError, "turned off"):
            services.reopen_set(night.session.pk, night.host, "why")
        services.close_night(night.session.night_id, night.host)
        with self.assertRaisesMessage(RuleError, "turned off"):
            services.reopen_night(night.session.night_id, night.host, "why")

    def test_a_reopened_set_with_a_later_set_cannot_resume_play(self):
        two = TwoSets()
        services.reopen_set(two.first.pk, two.host, "wrong count")
        with self.assertRaisesMessage(RuleError, "later set"):
            games.transition(two.first.pk, two.host, "resume")


class MissedBuyInTests(TestCase):
    def test_host_adds_a_buy_in_to_a_reopened_set(self):
        night = finalized()
        services.reopen_set(night.session.pk, night.host, "B's rebuy was never recorded")
        night.buy("B", 500)
        self.assertEqual(night.line("B").buy_in_total, 150000)
        # B's cash-out stands: the rebuy was played, not handed back.
        self.assertTrue(night.line("B").is_cashed_out)
        recash(night, "A", 2100)
        self.assertEqual(services.finalize(night.session.pk, night.host).revision, 2)
        self.assertEqual(nets(night.session), {"A": 110000, "B": -80000, "C": -30000})

    def test_a_player_who_left_can_get_the_missed_buy_in(self):
        night = Night("A", "B")
        night.buy("A", 1000)
        night.buy("B", 1000)
        night.cash("B", 0, left=True)
        night.go("reconciliation")
        night.cash("A", 2000)
        services.finalize(night.session.pk, night.host)
        services.reopen_set(night.session.pk, night.host, "B rebought once more")
        night.buy("B", 1000)
        self.assertEqual(night.line("B").buy_in_total, 200000)

    def test_an_ordinary_count_up_still_refuses_a_buy_in(self):
        night = Night("A", "B")
        night.buy("A", 1000)
        night.go("reconciliation")
        with self.assertRaisesMessage(RuleError, "only while the set is open or running"):
            night.buy("B", 1000)

    def test_a_player_cannot_rebuy_in_a_reopened_set(self):
        night = Night("A")
        member = night.add_login_player("P")
        night.buy("A", 1000)
        night.buy("P", 1000)
        night.go("reconciliation")
        night.cash("A", 1500)
        night.cash("P", 500)
        services.finalize(night.session.pk, night.host)
        services.reopen_set(night.session.pk, night.host, "why")
        with self.assertRaises(RuleError):
            ledger.record_buy_in(night.session.pk, member, night.players["P"].pk, 100000, uuid.uuid4())


class ReopenNightTests(TestCase):
    def closed(self):
        two = TwoSets()
        plan = services.close_night(two.night_id, two.host)
        return two, plan

    def night(self, two):
        return GameNight.objects.get(pk=two.night_id)

    def test_session_is_open_again_and_the_plan_is_kept(self):
        two, plan = self.closed()
        versions = {s.pk: s.version for s in GameSession.objects.filter(night_id=two.night_id)}
        services.reopen_night(two.night_id, two.host, "closed too early")
        night = self.night(two)
        self.assertEqual((night.status, night.closed_at), ("open", None))
        plan.refresh_from_db()
        self.assertFalse(plan.is_current)
        self.assertEqual((plan.void_reason, plan.voided_by), ("closed too early", two.host.user))
        self.assertTrue(Transfer.objects.filter(plan=plan).exists())
        for session in GameSession.objects.filter(night_id=two.night_id):
            self.assertGreater(session.version, versions[session.pk])
        event = AuditEvent.objects.get(action="night.reopened")
        self.assertEqual(event.reason, "closed too early")
        outcome = queries.night_outcome(night)
        self.assertEqual((outcome.plan, outcome.transfers), (None, []))

    def test_refused_while_a_transfer_is_marked_paid(self):
        two, plan = self.closed()
        transfer = plan.transfers.first()
        services.mark_paid(two.night_id, two.host, transfer.pk, uuid.uuid4())
        with self.assertRaisesMessage(RuleError, "1 transfer is marked paid. Mark it unpaid first."):
            services.reopen_night(two.night_id, two.host, "why")
        self.assertTrue(self.night(two).is_closed)
        services.mark_unpaid(two.night_id, two.host, transfer.pk)
        services.reopen_night(two.night_id, two.host, "why")
        self.assertFalse(self.night(two).is_closed)
        self.assertEqual(Payment.objects.filter(transfer=transfer).count(), 1)  # the reversed mark stays

    def test_reason_required_host_only_and_repeated_tap(self):
        two, _ = self.closed()
        with self.assertRaisesMessage(RuleError, "reason"):
            services.reopen_night(two.night_id, two.host, "")
        with self.assertRaises(NotAllowed):
            services.reopen_night(two.night_id, add_player(two.night.group, "Player"), "why")
        services.reopen_night(two.night_id, two.host, "why")
        services.reopen_night(two.night_id, two.host, "why")
        self.assertEqual(AuditEvent.objects.filter(action="night.reopened").count(), 1)

    def test_close_again_writes_a_new_plan_from_corrected_results(self):
        two, first = self.closed()
        services.reopen_night(two.night_id, two.host, "set 1 miscounted")
        services.reopen_set(two.first.pk, two.host, "A had 1,500, B 800")
        night = two.night
        recash(night, "A", 1500)
        recash(night, "B", 800)
        services.finalize(two.first.pk, two.host)
        second = services.close_night(two.night_id, two.host)
        self.assertNotEqual(second.pk, first.pk)
        self.assertEqual(SettlementPlan.objects.filter(night_id=two.night_id, is_current=True).get(), second)
        outcome = queries.night_outcome(self.night(two))
        self.assertEqual(outcome.plan, second)
        # Set 1: A +500, B −200, C −300. Set 2: A −400, B +400. Over both: A +100, B +200, C −300.
        balances = {}
        for t in outcome.transfers:
            balances[t.payer.display_name] = balances.get(t.payer.display_name, 0) - t.amount
            balances[t.payee.display_name] = balances.get(t.payee.display_name, 0) + t.amount
        self.assertEqual(balances, {"A": 10000, "B": 20000, "C": -30000})
        self.assertTrue(all(t.paid is None for t in outcome.transfers))

    def test_a_retired_transfer_cannot_be_marked_paid(self):
        two, first = self.closed()
        old = first.transfers.first()
        services.reopen_night(two.night_id, two.host, "why")
        services.close_night(two.night_id, two.host)
        with self.assertRaisesMessage(RuleError, "not in this session"):
            services.mark_paid(two.night_id, two.host, old.pk, uuid.uuid4())

    def test_another_set_can_be_played_after_reopening(self):
        two, _ = self.closed()
        with self.assertRaises(RuleError):
            games.start_next_set(two.night_id, two.host)
        services.reopen_night(two.night_id, two.host, "one more set")
        third = games.start_next_set(two.night_id, two.host)
        self.assertEqual(third.set_number, 3)

    def test_readers_show_only_the_current_list(self):
        two, first = self.closed()
        members = [p.member_id for p in two.night.players.values()]
        owed = len(queries.unpaid_transfers(members))
        self.assertGreater(owed, 0)
        services.reopen_night(two.night_id, two.host, "why")
        night = self.night(two)
        self.assertEqual(queries.unpaid_transfers(members), [])
        self.assertEqual(queries.unpaid_in(night), [])
        self.assertEqual(queries.settle_states([night.pk])[night.pk].transfers, 0)
        second = services.close_night(two.night_id, two.host)
        current = set(second.transfers.values_list("pk", flat=True))
        self.assertEqual({t.pk for t in queries.unpaid_transfers(members)}, current)
        self.assertEqual({t.pk for t in queries.unpaid_in(night)}, current)
        self.assertEqual(queries.settle_states([night.pk])[night.pk].transfers, len(current))

    def test_stats_leave_and_return(self):
        two, _ = self.closed()
        group = two.night.group
        self.assertEqual(queries.stat_results(group).count(), 6)
        services.reopen_night(two.night_id, two.host, "why")
        self.assertEqual(queries.stat_results(group).count(), 0)
        services.close_night(two.night_id, two.host)
        self.assertEqual(queries.stat_results(group).count(), 6)


class ReopenViewTests(TestCase):
    def setUp(self):
        self.night = finalized()
        self.client.force_login(self.night.host.user)

    def test_host_reopens_the_set_from_the_page(self):
        session = self.night.session
        page = self.client.get(reverse("session", args=[session.pk]))
        self.assertContains(page, reverse("session_reopen", args=[session.pk]))
        self.client.post(reverse("session_reopen", args=[session.pk]), {"reason": "wrong count"})
        self.assertEqual(self.night.refresh().state, "reconciliation")
        page = self.client.get(reverse("session", args=[session.pk]))
        self.assertContains(page, "Reopened to correct")
        self.assertContains(page, "wrong count")

    def test_corrected_line_on_the_final_page_and_revisions_in_the_log(self):
        session = self.night.session
        services.reopen_set(session.pk, self.night.host, "A had 1,500")
        recash(self.night, "A", 1500)
        recash(self.night, "B", 800)
        services.finalize(session.pk, self.night.host)
        page = self.client.get(reverse("session", args=[session.pk]))
        self.assertContains(page, "Corrected")
        self.assertContains(page, "A had 1,500")
        log = self.client.get(reverse("session_log", args=[session.pk]))
        self.assertContains(log, "Replaced")
        self.assertContains(log, "A had 1,500")

    def test_closed_session_offers_reopen_and_the_set_points_to_it(self):
        session = self.night.session
        plan = services.close_night(session.night_id, self.night.host)
        set_page = self.client.get(reverse("session", args=[session.pk]))
        self.assertNotContains(set_page, reverse("session_reopen", args=[session.pk]))
        self.assertContains(set_page, "Reopen the session first")
        url = reverse("night_reopen", args=[session.night_id])
        self.assertContains(self.client.get(reverse("night", args=[session.night_id])), url)
        services.mark_paid(session.night_id, self.night.host, plan.transfers.first().pk, uuid.uuid4())
        page = self.client.get(reverse("night", args=[session.night_id]))
        self.assertNotContains(page, url)
        self.assertContains(page, "Mark it unpaid first")
        services.mark_unpaid(session.night_id, self.night.host, plan.transfers.first().pk)
        self.client.post(url, {"reason": "closed too early"})
        self.assertFalse(GameNight.objects.get(pk=session.night_id).is_closed)
        self.assertContains(self.client.get(reverse("night", args=[session.night_id])), "closed too early")

    def test_players_and_strangers(self):
        session = self.night.session
        player = add_player(self.night.group, "Player")
        self.client.force_login(player.user)
        self.assertNotContains(self.client.get(reverse("session", args=[session.pk])), "Reopen set")
        self.client.post(reverse("session_reopen", args=[session.pk]), {"reason": "why"})
        self.assertEqual(self.night.refresh().state, "finalized")
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.post(reverse("session_reopen", args=[session.pk]), {"reason": "why"}).status_code, 404)
        self.assertEqual(self.client.post(reverse("night_reopen", args=[session.night_id]), {"reason": "why"}).status_code, 404)

    @override_settings(REOPENING=False)
    def test_switch_off_hides_the_controls(self):
        session = self.night.session
        self.assertNotContains(self.client.get(reverse("session", args=[session.pk])), "Reopen set")
        services.close_night(session.night_id, self.night.host)
        self.assertNotContains(self.client.get(reverse("night", args=[session.night_id])), "Reopen session")
