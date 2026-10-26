"""Payments made at the table while a session is open, and how closing subtracts them (ADR 0002)."""

import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_user
from ledger.models import PlayerResult
from ledger.tests.test_balance import worked_example
from settlement import queries, services
from settlement.models import Payment, PaymentReversal, Transfer

from .test_carried import Club


class TablePaymentTests(TestCase):
    """The worked example: A +₱600, B −₱300, C −₱300. Closed with no payment: B → A ₱300, C → A ₱300."""

    def setUp(self):
        self.night = worked_example()
        self.host = self.night.host
        self.game_night = self.night.session.night
        self.a, self.b, self.c = (self.night.players[name].member for name in "ABC")

    def pay(self, payer, payee, pesos, request_id=None):
        return services.record_table_payment(
            self.game_night.pk, self.host, payer.pk, payee.pk, pesos * 100, request_id or uuid.uuid4()
        )

    def close(self):
        services.finalize(self.night.session.pk, self.host)
        services.close_night(self.game_night.pk, self.host)
        names = {self.a.pk: "A", self.b.pk: "B", self.c.pk: "C"}
        rows = Transfer.objects.filter(plan__night=self.game_night, plan__is_current=True).order_by("position")
        return {(names[t.payer_id], names[t.payee_id]): t.amount // 100 for t in rows}

    def test_a_player_paid_in_full_at_the_table_has_no_transfer(self):
        self.pay(self.b, self.a, 300)
        self.assertEqual(self.close(), {("C", "A"): 300})

    def test_a_part_payment_leaves_the_rest(self):
        self.pay(self.b, self.a, 100)
        self.assertEqual(self.close(), {("B", "A"): 200, ("C", "A"): 300})

    def test_an_overpayment_flows_back(self):
        self.pay(self.b, self.a, 500)
        self.assertEqual(sorted(self.close().items()), [(("C", "A"), 100), (("C", "B"), 200)])

    def test_a_payment_between_two_losers_moves_the_debt(self):
        self.pay(self.c, self.b, 100)  # C hands B ₱100: C now owes ₱200 in all, B ₱400
        self.assertEqual(self.close(), {("B", "A"): 400, ("C", "A"): 200})

    def test_an_undone_payment_counts_for_nothing(self):
        payment = self.pay(self.b, self.a, 300)
        services.reverse_table_payment(self.game_night.pk, self.host, payment.pk, "wrong player")
        self.assertEqual(self.close(), {("B", "A"): 300, ("C", "A"): 300})
        self.assertEqual(PaymentReversal.objects.get().reason, "wrong player")

    def test_results_do_not_change(self):
        services.finalize(self.night.session.pk, self.host)
        before = list(PlayerResult.objects.order_by("pk").values_list("net", flat=True))
        self.pay(self.b, self.a, 300)
        services.close_night(self.game_night.pk, self.host)
        self.assertEqual(list(PlayerResult.objects.order_by("pk").values_list("net", flat=True)), before)

    def test_reopen_and_close_again_gives_the_same_list(self):
        self.pay(self.b, self.a, 300)
        first = self.close()
        with self.settings(REOPENING=True):
            services.reopen_night(self.game_night.pk, self.host, "check")
        services.close_night(self.game_night.pk, self.host)
        rows = Transfer.objects.filter(plan__night=self.game_night, plan__is_current=True)
        self.assertEqual([(t.payer_id, t.payee_id, t.amount // 100) for t in rows], [(self.c.pk, self.a.pk, 300)])
        self.assertEqual(first, {("C", "A"): 300})

    def test_a_repeated_tap_records_one_payment(self):
        request_id = uuid.uuid4()
        first = self.pay(self.b, self.a, 300, request_id)
        self.assertEqual(self.pay(self.b, self.a, 300, request_id).pk, first.pk)
        self.assertEqual(Payment.objects.count(), 1)

    def test_a_payment_is_audited_and_refreshes_open_set_pages(self):
        version = self.night.refresh().version
        payment = self.pay(self.b, self.a, 300)
        self.assertGreater(self.night.refresh().version, version)
        self.assertTrue(AuditEvent.objects.filter(action="payment.recorded").exists())
        services.reverse_table_payment(self.game_night.pk, self.host, payment.pk, "mistake")
        self.assertTrue(AuditEvent.objects.filter(action="payment.reversed").exists())

    def test_only_the_host_records_or_undoes(self):
        player = add_player(self.night.group, "Dee")
        with self.assertRaises(NotAllowed):
            services.record_table_payment(self.game_night.pk, player, self.b.pk, self.a.pk, 100, uuid.uuid4())
        payment = self.pay(self.b, self.a, 300)
        with self.assertRaises(NotAllowed):
            services.reverse_table_payment(self.game_night.pk, player, payment.pk, "no")

    def test_rules_on_the_payment(self):
        stranger = add_player(self.night.group, "Dee")  # in the group, not at this session
        cases = [
            (self.b, self.b, 100),
            (self.b, stranger, 100),
            (self.b, self.a, 0),
            (self.b, self.a, -100),
        ]
        for payer, payee, pesos in cases:
            with self.subTest(payer=payer, payee=payee, pesos=pesos), self.assertRaises(RuleError):
                self.pay(payer, payee, pesos)
        with self.assertRaises(RuleError):
            services.record_table_payment(self.game_night.pk, self.host, self.b.pk, self.a.pk, "100", uuid.uuid4())
        self.assertEqual(Payment.objects.count(), 0)

    def test_undo_needs_a_reason(self):
        payment = self.pay(self.b, self.a, 300)
        with self.assertRaises(RuleError):
            services.reverse_table_payment(self.game_night.pk, self.host, payment.pk, "  ")
        services.reverse_table_payment(self.game_night.pk, self.host, payment.pk, "mistake")
        services.reverse_table_payment(self.game_night.pk, self.host, payment.pk, "mistake")  # a repeated tap
        self.assertEqual(PaymentReversal.objects.count(), 1)

    def test_nothing_changes_after_the_session_is_closed(self):
        payment = self.pay(self.b, self.a, 100)
        self.close()
        with self.assertRaises(RuleError):
            self.pay(self.b, self.a, 100)
        with self.assertRaises(RuleError):
            services.reverse_table_payment(self.game_night.pk, self.host, payment.pk, "late")

    def test_a_paid_mark_cannot_be_undone_as_a_table_payment(self):
        self.close()
        transfer = Transfer.objects.first()
        mark = services.mark_paid(self.game_night.pk, self.host, transfer.pk, uuid.uuid4())
        with self.settings(REOPENING=True):
            services.mark_unpaid(self.game_night.pk, self.host, transfer.pk)
            services.reopen_night(self.game_night.pk, self.host, "check")
        with self.assertRaises(RuleError):
            services.reverse_table_payment(self.game_night.pk, self.host, mark.pk, "no")

    def test_the_database_needs_both_players_on_a_table_payment(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Payment.objects.create(
                night=self.game_night, payer=self.b, payee=None, amount=100, request_id=uuid.uuid4(),
                recorded_by=self.host.user,
            )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Payment.objects.create(
                night=self.game_night, payer=self.b, payee=self.b, amount=100, request_id=uuid.uuid4(),
                recorded_by=self.host.user,
            )

    def test_the_session_page_mark_changes_while_open(self):
        before = queries.night_stamp(self.game_night)
        payment = self.pay(self.b, self.a, 300)
        recorded = queries.night_stamp(self.game_night)
        self.assertNotEqual(recorded, before)
        services.reverse_table_payment(self.game_night.pk, self.host, payment.pk, "mistake")
        self.assertNotEqual(queries.night_stamp(self.game_night), recorded)

    def test_the_outcome_lists_table_payments_apart(self):
        self.pay(self.b, self.a, 300)
        outcome = queries.night_outcome(self.game_night)
        self.assertEqual([(p.payer_id, p.amount) for p in outcome.table_payments], [(self.b.pk, 30000)])
        self.close()
        outcome = queries.night_outcome(self.game_night)
        self.assertEqual(len(outcome.table_payments), 1)
        self.assertEqual(outcome.status, "unsettled")  # the table payment is not a paid mark


class TablePaymentWithCarryTests(TestCase):
    def test_a_carried_transfer_and_a_table_payment_still_clear(self):
        club = Club("Ana", "Ben", "Carlo")
        first = club.closed({"Ana": -500, "Ben": 500})  # Ana owes Ben 500
        second = club.play({"Ana": 300, "Ben": -100, "Carlo": -200})
        members = club.members
        services.record_table_payment(second, club.host, members["Carlo"].pk, members["Ana"].pk, 20000, uuid.uuid4())
        club.close(second, carry=club.unpaid(first))
        # Ana: +300 − 500 carried − 200 received = −400. Ben: −100 + 500 = +400. Carlo: −200 + 200 = 0.
        self.assertEqual(club.transfers(second), {("Ana", "Ben"): 400})


class TablePaymentViewTests(TestCase):
    """A running set: A and B play; ben has a login, wins ₱400 and leaves early."""

    def setUp(self):
        from ledger.tests.helpers import Night

        self.night = Night("A", "B")
        self.ben = self.night.add_login_player("ben")
        for name in ("A", "B", "ben"):
            self.night.buy(name, 1000)
        self.night.cash("ben", 1400, left=True)
        self.night_id = self.night.session.night_id
        self.a = self.night.players["A"].member
        self.page_url = reverse("night", args=[self.night_id])
        self.form_url = reverse("table_payment", args=[self.night_id])

    def post(self, **data):
        return self.client.post(self.form_url, {"request_id": str(uuid.uuid4()), **data})

    def test_host_records_from_the_session_page_and_undoes(self):
        self.client.force_login(self.night.host.user)
        page = self.client.get(self.page_url)
        self.assertContains(page, "Paid at the table")
        self.assertContains(page, "Record a payment")
        response = self.post(payer=self.a.pk, payee=self.ben.pk, amount="400")
        self.assertRedirects(response, self.page_url, fetch_redirect_response=False)
        payment = Payment.objects.get()
        self.assertEqual((payment.payer, payment.payee, payment.amount, payment.transfer), (self.a, self.ben, 40000, None))
        page = self.client.get(self.page_url)
        self.assertContains(page, "recorded by")
        self.client.post(reverse("table_payment_undo", args=[self.night_id, payment.pk]), {"reason": "wrong player"})
        payment.refresh_from_db()
        self.assertFalse(payment.active)
        self.assertContains(self.client.get(self.page_url), "undone: wrong player")

    def test_a_refusal_keeps_the_values_on_the_fallback_page(self):
        self.client.force_login(self.night.host.user)
        response = self.post(payer=self.a.pk, payee=self.a.pk, amount="400")
        self.assertEqual(response.status_code, 422)
        self.assertContains(response, "Choose two different players.", status_code=422)
        self.assertContains(response, 'value="400"', status_code=422)
        response = self.post(payer=self.a.pk, payee=self.ben.pk, amount="abc")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(Payment.objects.count(), 0)

    def test_the_leaver_link_fills_in_the_form_and_returns_to_the_set(self):
        self.client.force_login(self.night.host.user)
        set_page = self.client.get(reverse("session", args=[self.night.session.pk]))
        self.assertContains(set_page, "Paid at the table?")
        page = self.client.get(self.form_url, {"leaver": self.ben.pk, "net": 40000, "from_set": self.night.session.pk})
        self.assertContains(page, f'<option value="{self.ben.pk}" selected>', count=1)
        self.assertContains(page, 'value="400"')
        response = self.post(payer=self.a.pk, payee=self.ben.pk, amount="400", from_set=self.night.session.pk)
        self.assertRedirects(response, reverse("session", args=[self.night.session.pk]), fetch_redirect_response=False)

    def test_a_loser_who_leaves_is_the_payer(self):
        self.client.force_login(self.night.host.user)
        page = self.client.get(self.form_url, {"leaver": self.a.pk, "net": -25050})
        self.assertContains(page, 'value="250.50"')
        self.assertContains(page, f'<option value="{self.a.pk}" selected>', count=1)

    def test_a_player_sees_their_own_payment_but_no_form(self):
        services.record_table_payment(self.night_id, self.night.host, self.a.pk, self.ben.pk, 40000, uuid.uuid4())
        self.client.force_login(self.ben.user)
        page = self.client.get(self.page_url)
        self.assertContains(page, "Paid at the table")
        self.assertNotContains(page, "Record a payment")
        self.assertNotContains(page, "Undo payment")
        self.assertEqual(self.client.get(self.form_url).status_code, 403)
        self.assertEqual(self.post(payer=self.a.pk, payee=self.ben.pk, amount="1").status_code, 403)

    def test_a_player_sees_nothing_when_there_is_no_payment(self):
        self.client.force_login(self.ben.user)
        self.assertNotContains(self.client.get(self.page_url), "Paid at the table")

    def test_another_group_gets_404(self):
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.get(self.form_url).status_code, 404)
        self.assertEqual(self.post(payer=self.a.pk, payee=self.ben.pk, amount="1").status_code, 404)

    def test_a_closed_session_refuses_with_a_message(self):
        self.night.go("reconciliation")
        self.night.cash("A", 800)
        self.night.cash("B", 800)
        services.finalize(self.night.session.pk, self.night.host)
        services.close_night(self.night_id, self.night.host)
        self.client.force_login(self.night.host.user)
        self.assertContains(self.client.get(self.form_url), "The session is closed.")
        response = self.post(payer=self.a.pk, payee=self.ben.pk, amount="400")
        self.assertContains(response, "The session is closed.", status_code=422)
