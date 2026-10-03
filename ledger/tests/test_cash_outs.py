import uuid

from django.test import TestCase
from django.urls import reverse

from games import services as games
from games.models import Participant
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

    def test_cash_out_is_an_amount_in_pesos(self):
        cash_out = self.night.cash("A", 1600)
        self.assertEqual(cash_out.amount, 160000)
        self.assertFalse(hasattr(cash_out, "chips"))

    def test_player_cashes_out_in_several_steps(self):
        self.night.cash("A", 600)
        self.night.cash("A", 400)
        self.night.cash("A", 600)
        line = self.night.line("A")
        self.assertEqual((len(line.cash_outs), line.cashed_out), (3, 160000))
        self.assertEqual(Participant.objects.get(pk=self.night.players["A"].pk).status, "joined")

    def test_amount_in_play_falls_as_players_cash_out(self):
        summary = queries.summary(self.night.session)
        self.assertEqual((summary.total, summary.in_play), (250000, 250000))
        self.night.cash("B", 700, left=True)
        summary = queries.summary(self.night.session)
        self.assertEqual((summary.cashed_out, summary.in_play), (70000, 180000))
        self.assertEqual(summary.total, 250000)  # buy-ins do not change when a player leaves
        self.assertEqual(summary.line_for(self.night.players["B"].pk).participant.status, "left")

    def test_zero_is_a_real_cash_out(self):
        self.assertFalse(self.night.line("C").has_cash_out)
        self.night.cash("C", 0)
        line = self.night.line("C")
        self.assertTrue(line.has_cash_out)
        self.assertEqual(line.cashed_out, 0)

    def test_centavos_are_kept_exactly(self):
        services.record_cash_out(self.night.session.pk, self.night.host, self.night.players["A"].pk, 160050, uuid.uuid4())
        self.assertEqual(self.night.line("A").cashed_out, 160050)

    def test_reversal_keeps_the_row(self):
        wrong = self.night.cash("A", 999)
        with self.assertRaises(RuleError):
            services.reverse_cash_out(self.night.session.pk, self.night.host, wrong.pk, "")
        services.reverse_cash_out(self.night.session.pk, self.night.host, wrong.pk, "miscounted")
        services.reverse_cash_out(self.night.session.pk, self.night.host, wrong.pk, "again")
        self.night.cash("A", 1600)
        line = self.night.line("A")
        self.assertEqual((line.cashed_out, len(line.reversed_cash_outs)), (160000, 1))
        self.assertEqual((CashOut.objects.count(), CashOutReversal.objects.count()), (2, 1))

    def test_repeated_request_id_records_once(self):
        request_id = uuid.uuid4()
        self.night.cash("A", 1600, request_id)
        self.night.cash("A", 1600, request_id)
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
        self.night.cash("A", 1600)  # counting up: allowed

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

    def test_host_types_a_peso_amount(self):
        self.client.force_login(self.night.host.user)
        page = self.client.post(self.url, {"participant_id": self.night.players["A"].pk, "amount": "1,600", "left": "1"}, follow=True)
        self.assertContains(page, "Cashed out ₱1,600")
        self.assertContains(page, "Still in play")
        self.assertContains(page, ">₱400<")
        self.assertContains(page, "Left")
        self.assertContains(page, "Cash-out in pesos")
        self.assertNotContains(page, "chips")

    def test_bad_input_shows_a_message(self):
        self.client.force_login(self.night.host.user)
        page = self.client.post(self.url, {"participant_id": self.night.players["A"].pk, "amount": "lots"}, follow=True)
        self.assertContains(page, "Enter an amount in pesos")
        self.assertEqual(CashOut.objects.count(), 0)

    def test_player_sees_own_cash_out_but_cannot_record(self):
        self.night.cash("ben", 250)
        self.client.force_login(self.ben.user)
        page = self.client.get(reverse("session", args=[self.night.session.pk]))
        self.assertContains(page, "Cashed out ₱250")
        self.assertNotContains(page, "cashouts/add")
        response = self.client.post(self.url, {"participant_id": self.night.players["ben"].pk, "amount": "99999"})
        self.assertEqual(response.status_code, 403)
        cash_out = CashOut.objects.get()
        self.assertEqual(self.client.post(reverse("cash_out_reverse", args=[self.night.session.pk, cash_out.pk]), {"reason": "x"}).status_code, 403)
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.post(self.url, {"amount": "1"}).status_code, 404)
        self.assertEqual(CashOut.objects.count(), 1)
