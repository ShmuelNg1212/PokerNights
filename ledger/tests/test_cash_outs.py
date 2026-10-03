import uuid

from django.test import TestCase
from django.urls import reverse

from games import services as games
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import make_user
from ledger import queries, services
from ledger.models import CashOut, CashOutReversal

from .helpers import Night


class CashOutTests(TestCase):
    def setUp(self):
        self.night = Night("A", "B", "C")
        self.night.buy("A", 1000)
        self.night.buy("B", 1000)
        self.night.buy("C", 500)

    def test_player_cashes_out_in_several_steps(self):
        self.night.cash("A", 6000)
        self.night.cash("A", 4000)
        self.night.cash("A", 6000)
        line = self.night.line("A")
        self.assertEqual((len(line.cash_outs), line.chips_cashed), (3, 16000))
        self.assertEqual(line.cash_value, (160000, True))
        self.assertEqual(self.night.players["A"].__class__.objects.get(pk=self.night.players["A"].pk).status, "joined")

    def test_chips_in_play_fall_as_players_cash_out(self):
        summary = queries.summary(self.night.session)
        self.assertEqual((summary.chips_issued, summary.chips_in_play), (25000, 25000))
        self.night.cash("B", 7000, left=True)
        summary = queries.summary(self.night.session)
        self.assertEqual((summary.chips_cashed, summary.chips_in_play), (7000, 18000))
        self.assertEqual(summary.total_centavos, 250000)  # buy-ins do not change when chips leave
        self.assertEqual(summary.line_for(self.night.players["B"].pk).participant.status, "left")

    def test_zero_is_a_real_cash_out(self):
        self.assertFalse(self.night.line("C").has_cash_out)
        self.night.cash("C", 0)
        line = self.night.line("C")
        self.assertTrue(line.has_cash_out)
        self.assertEqual(line.chips_cashed, 0)

    def test_inexact_value_is_marked(self):
        # ₱1,000 for 30,000 chips: one chip is worth a third of a centavo more than 3.
        night = Night("X", chips_per_buy_in=30000)
        night.buy("X", 1000)
        night.cash("X", 100)
        self.assertEqual(night.line("X").cash_value, (333, False))

    def test_reversal_keeps_the_row(self):
        wrong = self.night.cash("A", 9999)
        with self.assertRaises(RuleError):
            services.reverse_cash_out(self.night.session.pk, self.night.host, wrong.pk, "")
        services.reverse_cash_out(self.night.session.pk, self.night.host, wrong.pk, "miscounted")
        services.reverse_cash_out(self.night.session.pk, self.night.host, wrong.pk, "again")
        self.night.cash("A", 16000)
        line = self.night.line("A")
        self.assertEqual((line.chips_cashed, len(line.reversed_cash_outs)), (16000, 1))
        self.assertEqual((CashOut.objects.count(), CashOutReversal.objects.count()), (2, 1))

    def test_repeated_request_id_records_once(self):
        request_id = uuid.uuid4()
        self.night.cash("A", 16000, request_id)
        self.night.cash("A", 16000, request_id)
        self.assertEqual(CashOut.objects.count(), 1)

    def test_rules(self):
        night = self.night
        with self.assertRaises(RuleError):
            night.cash("A", -1)
        with self.assertRaises(RuleError):
            services.record_cash_out(night.session.pk, night.host, night.players["A"].pk, 10.5, uuid.uuid4())
        ben = night.add_login_player("ben")
        with self.assertRaisesMessage(RuleError, "no buy-in"):
            night.cash("ben", 100)
        with self.assertRaises(NotAllowed):
            services.record_cash_out(night.session.pk, ben, night.players["A"].pk, 100, uuid.uuid4())
        self.assertEqual(CashOut.objects.count(), 0)

    def test_states(self):
        early = Night("X", state="open")
        early.buy("X", 1000)
        with self.assertRaises(RuleError):
            early.cash("X", 100)  # the game has not started
        self.night.go("reconciliation")
        self.night.cash("A", 16000)  # counting chips: allowed

    def test_player_with_a_cash_out_cannot_be_withdrawn(self):
        self.night.cash("A", 100)
        with self.assertRaises(RuleError):
            games.withdraw_participant(self.night.session.pk, self.night.host, self.night.players["A"].pk)


class CashOutViewTests(TestCase):
    def setUp(self):
        self.night = Night("A")
        self.ben = self.night.add_login_player("ben")
        self.night.buy("A", 1000)
        self.night.buy("ben", 1000)
        self.url = reverse("cash_out_add", args=[self.night.session.pk])

    def test_host_records_and_the_page_keeps_chips_and_pesos_apart(self):
        self.client.force_login(self.night.host.user)
        page = self.client.post(self.url, {"participant_id": self.night.players["A"].pk, "chips": "16,000", "left": "1"}, follow=True)
        self.assertContains(page, "Cashed out 16,000 chips (₱1,600)")
        self.assertContains(page, "Chips in play")
        self.assertContains(page, ">4,000<")
        self.assertContains(page, "Left")

    def test_bad_input_shows_a_message(self):
        self.client.force_login(self.night.host.user)
        page = self.client.post(self.url, {"participant_id": self.night.players["A"].pk, "chips": "lots"}, follow=True)
        self.assertContains(page, "Enter the number of chips")
        self.assertEqual(CashOut.objects.count(), 0)

    def test_player_sees_own_cash_out_but_cannot_record(self):
        self.night.cash("ben", 2500)
        self.client.force_login(self.ben.user)
        page = self.client.get(reverse("session", args=[self.night.session.pk]))
        self.assertContains(page, "Cashed out 2,500 chips (₱250)")
        self.assertNotContains(page, "cashouts/add")
        response = self.client.post(self.url, {"participant_id": self.night.players["ben"].pk, "chips": "99999"})
        self.assertEqual(response.status_code, 403)
        cash_out = CashOut.objects.get()
        self.assertEqual(self.client.post(reverse("cash_out_reverse", args=[self.night.session.pk, cash_out.pk]), {"reason": "x"}).status_code, 403)
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.post(self.url, {"chips": "1"}).status_code, 404)
        self.assertEqual(CashOut.objects.count(), 1)
