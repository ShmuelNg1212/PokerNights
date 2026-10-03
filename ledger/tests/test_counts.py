"""Final counts are confirmed apart from cash-outs. "Not counted" is never zero."""

import datetime
import uuid
from unittest import mock

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from games import clock
from games import services as games
from games.models import PlayInterval
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_group, make_user
from ledger import queries, services
from ledger.models import CashOut, FinalCount

from .helpers import Night


def counting(*names, buy_in=1000):
    """A set in the counting stage: everyone bought in, nobody is counted or cashed out."""
    night = Night(*names or ("A", "B", "C"))
    for name in night.players:
        night.buy(name, buy_in)
    night.go("reconciliation")
    return night


def count(night, name, pesos, request_id=None):
    return services.confirm_count(
        night.session.pk, night.host, night.players[name].pk, pesos * night.scale, request_id or uuid.uuid4()
    )


def statuses(night):
    return {line.participant.member.display_name: line.status for line in queries.summary(night.session).money_lines}


class FinalCountTests(TestCase):
    def test_zero_is_a_count_and_no_count_is_not_zero(self):
        night = counting()
        self.assertEqual(statuses(night), {"A": "awaiting", "B": "awaiting", "C": "awaiting"})
        count(night, "C", 0)
        self.assertEqual(statuses(night), {"A": "awaiting", "B": "awaiting", "C": "ready"})
        self.assertEqual(night.line("C").count.amount, 0)
        self.assertIsNone(night.line("A").count)
        # A count is not a cash-out: no money record exists yet.
        self.assertEqual(CashOut.objects.count(), 0)
        self.assertEqual(queries.summary(night.session).cashed_out, 0)

    def test_confirming_again_adds_a_version_and_keeps_the_old_row(self):
        night = counting()
        first = count(night, "A", 1500)
        second = count(night, "A", 1600)
        first.refresh_from_db()
        self.assertEqual((first.version, first.is_current, first.amount), (1, False, 150000))
        self.assertEqual((second.version, second.is_current, second.amount), (2, True, 160000))
        self.assertEqual(night.line("A").count.pk, second.pk)
        self.assertEqual(FinalCount.objects.count(), 2)
        with self.assertRaises(IntegrityError), transaction.atomic():
            FinalCount.objects.create(
                session=night.session, participant=night.players["A"], amount=1, version=3,
                request_id=uuid.uuid4(), confirmed_by=night.host.user,
            )  # a second current count for one player

    def test_repeated_request_confirms_once(self):
        night = counting()
        request_id = uuid.uuid4()
        first = count(night, "A", 1600, request_id)
        self.assertEqual(count(night, "A", 1600, request_id).pk, first.pk)
        self.assertEqual(FinalCount.objects.count(), 1)

    def test_clear_returns_the_player_to_awaiting(self):
        night = counting()
        count(night, "A", 1600)
        services.clear_count(night.session.pk, night.host, night.players["A"].pk)
        self.assertEqual(statuses(night)["A"], "awaiting")
        cleared = FinalCount.objects.get()
        self.assertEqual((cleared.is_current, cleared.voided_by), (False, night.host.user))
        self.assertEqual(count(night, "A", 1600).version, 2)  # versions keep rising

    def test_rules(self):
        night = counting()
        with self.assertRaises(RuleError):
            count(night, "A", -1)
        with self.assertRaises(RuleError):
            services.confirm_count(night.session.pk, night.host, night.players["A"].pk, 10.5, uuid.uuid4())
        ben = add_player(night.group, "ben")
        with self.assertRaises(NotAllowed):
            services.confirm_count(night.session.pk, ben, night.players["A"].pk, 100, uuid.uuid4())
        _, other_host = make_group("omar", "Other")
        with self.assertRaises(RuleError):
            services.confirm_count(night.session.pk, other_host, night.players["A"].pk, 100, uuid.uuid4())
        running = Night("X")
        running.buy("X", 1000)
        with self.assertRaisesMessage(RuleError, "after play has ended"):
            count(running, "X", 1000)
        self.assertEqual(FinalCount.objects.count(), 0)

    def test_player_without_a_buy_in_or_already_cashed_out_cannot_be_counted(self):
        night = Night("A", "Watcher")
        night.buy("A", 1000)
        night.go("reconciliation")
        with self.assertRaisesMessage(RuleError, "no buy-in"):
            count(night, "Watcher", 0)
        night.cash("A", 1000)
        with self.assertRaisesMessage(RuleError, "already cashed out"):
            count(night, "A", 1000)

    def test_count_is_audited_with_its_time_and_host(self):
        night = counting()
        count(night, "A", 1600)
        event = AuditEvent.objects.get(action="count.confirmed")
        self.assertEqual((event.actor, event.summary), (night.host.user, "Confirmed A's final count: ₱1,600"))


class CashOutKindTests(TestCase):
    def test_kind_follows_the_situation(self):
        night = Night("A", "B")
        night.buy("A", 1000)
        night.buy("B", 1000)
        self.assertEqual(night.cash("A", 300).kind, "partial")  # plays on
        self.assertEqual(night.cash("B", 400, left=True).kind, "final")  # leaves
        night.go("reconciliation")
        self.assertEqual(night.cash("A", 1300).kind, "final")  # play has ended
        self.assertEqual(statuses(night), {"A": "cashed_out", "B": "cashed_out"})

    def test_a_cashed_out_player_cannot_be_cashed_out_again(self):
        night = counting()
        night.cash("A", 1600)
        with self.assertRaisesMessage(RuleError, "already cashed out"):
            night.cash("A", 100)
        self.assertEqual(CashOut.objects.count(), 1)

    def test_individual_cash_out_while_counting_voids_an_unused_count(self):
        night = counting()
        count(night, "A", 1500)
        night.cash("A", 1600)  # the exception path, with another figure
        self.assertEqual(statuses(night)["A"], "cashed_out")
        self.assertFalse(FinalCount.objects.filter(is_current=True).exists())

    def test_partial_cash_out_during_play_does_not_satisfy_the_gate(self):
        night = Night("A", "B")
        night.buy("A", 1000)
        night.buy("B", 1000)
        night.cash("A", 2000)  # A takes chips off the table and plays on
        night.go("reconciliation")
        night.cash("B", 0)
        balance = queries.balance(night.session)
        self.assertFalse(balance.ok)
        self.assertFalse(balance.counted)
        self.assertIn("Not cashed out yet: A", balance.explanation)
        count(night, "A", 0)
        self.assertIn("Not cashed out yet: A", queries.balance(night.session).explanation)  # counted is not cashed out
        services.clear_count(night.session.pk, night.host, night.players["A"].pk)
        night.cash("A", 0)
        self.assertTrue(queries.balance(night.session).ok)

    def test_a_player_who_returns_or_rebuys_plays_on(self):
        night = Night("A", "B")
        night.buy("A", 1000)
        night.buy("B", 1000)
        night.cash("A", 0, left=True)  # busted and went home
        self.assertEqual(statuses(night)["A"], "cashed_out")
        games.set_left(night.session.pk, night.host, night.players["A"].pk, False)  # came back
        self.assertEqual(statuses(night)["A"], "awaiting")
        self.assertEqual(CashOut.objects.get().kind, "partial")
        night.cash("B", 500, left=True)
        games.set_left(night.session.pk, night.host, night.players["B"].pk, False)
        night.buy("B", 1000)
        self.assertEqual(statuses(night)["B"], "awaiting")
        self.assertTrue(AuditEvent.objects.filter(action="cash_out.reclassified").exists())


class ResumeTests(TestCase):
    """Q3: resume is allowed; uncashed counts are void; cashed-out players stay out."""

    def test_resume_voids_counts_that_are_not_cashed_out(self):
        night = counting()
        count(night, "A", 1600)
        count(night, "B", 700)
        night.cash("C", 700)
        games.transition(night.session.pk, night.host, "resume")
        self.assertEqual(FinalCount.objects.filter(is_current=True).count(), 0)
        self.assertEqual(FinalCount.objects.filter(voided_at__isnull=False).count(), 2)
        self.assertEqual(CashOut.objects.filter(kind="final").count(), 1)  # C stays cashed out
        self.assertIn("2 confirmed counts voided", AuditEvent.objects.get(action="count.voided_on_resume").summary)

    def test_cashed_out_player_gets_no_playing_time_after_a_resume(self):
        base = datetime.datetime(2026, 10, 9, 12, 0, tzinfo=datetime.timezone.utc)

        def at(minutes):
            return mock.patch("games.services.timezone.now", return_value=base + datetime.timedelta(minutes=minutes))

        with at(0):
            night = Night("A", "B")
        night.buy("A", 1000)
        night.buy("B", 1000)
        with at(60):
            night.go("reconciliation")
        night.cash("B", 500)
        with at(70):
            games.transition(night.session.pk, night.host, "resume")
        with at(100):
            games.transition(night.session.pk, night.host, "end")
        played = clock.player_seconds(night.session, base + datetime.timedelta(minutes=500))
        self.assertEqual(played[night.players["A"].pk] // 60, 90)
        self.assertEqual(played[night.players["B"].pk] // 60, 60)
        self.assertEqual(PlayInterval.objects.filter(participant=night.players["B"]).count(), 1)
        # B buys in again in a later resume: B is back in play and is timed again.
        with at(110):
            games.transition(night.session.pk, night.host, "resume")
        with at(115):
            night.buy("B", 1000)
        self.assertEqual(PlayInterval.objects.filter(participant=night.players["B"], ended_at__isnull=True).count(), 1)
        self.assertEqual(statuses(night)["B"], "awaiting")


class CountPageTests(TestCase):
    def setUp(self):
        self.night = counting()
        self.url = reverse("count_confirm", args=[self.night.session.pk])
        self.page_url = reverse("session", args=[self.night.session.pk])
        self.client.force_login(self.night.host.user)

    def post(self, name, amount):
        return self.client.post(self.url, {"participant_id": self.night.players[name].pk, "amount": amount}, follow=True)

    def test_page_shows_the_three_statuses(self):
        self.post("A", "1600")
        self.night.cash("B", 700)
        page = self.client.get(self.page_url)
        for text in ('data-status="ready">Ready to cash out', 'data-status="cashed_out">Cashed out', 'data-status="awaiting">Awaiting count',
                     "Counted ₱1,600", "Payment: at the end of the session", "Change count", "Confirm count"):
            self.assertContains(page, text)

    def test_zero_is_accepted_and_empty_is_refused(self):
        page = self.post("C", "0")
        self.assertContains(page, "Counted ₱0")
        page = self.post("A", "")
        self.assertContains(page, "Enter the final count. Type 0 for a player who has nothing left.")
        page = self.post("B", "   ")
        self.assertEqual(statuses(self.night), {"A": "awaiting", "B": "awaiting", "C": "ready"})
        self.assertContains(self.post("A", "lots"), "Enter an amount in pesos")

    def test_individual_cash_out_is_under_details_while_counting(self):
        page = self.client.get(self.page_url)
        self.assertContains(page, "Exception: cash this player out now, without a confirmed count.")
        self.assertContains(page, "cashouts/add")

    def test_clear_from_the_page(self):
        self.post("A", "1600")
        page = self.client.post(reverse("count_clear", args=[self.night.session.pk, self.night.players["A"].pk]), follow=True)
        self.assertContains(page, "Count cleared.")
        self.assertEqual(statuses(self.night)["A"], "awaiting")

    def test_player_sees_statuses_but_cannot_count(self):
        ben = add_player(self.night.group, "ben")
        self.client.force_login(ben.user)
        page = self.client.get(self.page_url)
        self.assertContains(page, "Awaiting count")
        self.assertNotContains(page, "counts/confirm")
        self.assertEqual(self.client.post(self.url, {"participant_id": self.night.players["A"].pk, "amount": "5"}).status_code, 403)
        self.assertEqual(self.client.post(reverse("count_clear", args=[self.night.session.pk, self.night.players["A"].pk])).status_code, 403)
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.post(self.url, {"amount": "5"}).status_code, 404)
        self.assertEqual(FinalCount.objects.count(), 0)

    def test_finalize_names_who_is_not_cashed_out(self):
        self.post("A", "1600")
        page = self.client.post(reverse("session_finalize", args=[self.night.session.pk]), follow=True)
        self.assertContains(page, "Not cashed out yet: A, B, C")
