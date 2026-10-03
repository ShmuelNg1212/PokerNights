import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_user
from ledger.models import PlayerResult
from ledger.tests.test_balance import worked_example
from settlement import queries, services
from settlement.models import Payment, PaymentReversal, Transfer


class PaidMarkTests(TestCase):
    def setUp(self):
        self.night = worked_example()
        services.finalize(self.night.session.pk, self.night.host)
        self.session, self.host = self.night.session, self.night.host
        self.game_night = self.session.night
        services.close_night(self.game_night.pk, self.host)
        self.b_to_a, self.c_to_a = Transfer.objects.order_by("position")

    def status(self):
        return queries.night_outcome(self.game_night).status

    def test_status_moves_from_unsettled_to_partly_to_settled(self):
        self.assertEqual(self.status(), "unsettled")
        payment = services.mark_paid(self.game_night.pk, self.host, self.b_to_a.pk, uuid.uuid4())
        self.assertEqual((payment.payer, payment.payee, payment.amount), (self.night.players["B"].member, self.night.players["A"].member, 30000))
        self.assertEqual(self.status(), "partly")
        outcome = queries.night_outcome(self.game_night)
        self.assertTrue(outcome.transfers[0].paid)
        self.assertIsNone(outcome.transfers[1].paid)  # the unpaid transfer stays visible
        services.mark_paid(self.game_night.pk, self.host, self.c_to_a.pk, uuid.uuid4())
        self.assertEqual(self.status(), "settled")

    def test_marking_twice_records_one_payment(self):
        request_id = uuid.uuid4()
        first = services.mark_paid(self.game_night.pk, self.host, self.b_to_a.pk, request_id)
        self.assertEqual(services.mark_paid(self.game_night.pk, self.host, self.b_to_a.pk, request_id).pk, first.pk)
        self.assertEqual(services.mark_paid(self.game_night.pk, self.host, self.b_to_a.pk, uuid.uuid4()).pk, first.pk)
        self.assertEqual(Payment.objects.count(), 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Payment.objects.create(
                night=self.game_night, payer=first.payer, payee=first.payee, amount=1, transfer=self.b_to_a,
                request_id=uuid.uuid4(), recorded_by=self.host.user,
            )

    def test_undo_keeps_the_record_and_allows_marking_again(self):
        services.mark_paid(self.game_night.pk, self.host, self.b_to_a.pk, uuid.uuid4())
        services.mark_unpaid(self.game_night.pk, self.host, self.b_to_a.pk, "wrong row")
        services.mark_unpaid(self.game_night.pk, self.host, self.b_to_a.pk)  # nothing to undo
        self.assertEqual(self.status(), "unsettled")
        self.assertEqual((Payment.objects.count(), PaymentReversal.objects.count()), (1, 1))
        services.mark_paid(self.game_night.pk, self.host, self.b_to_a.pk, uuid.uuid4())
        self.assertEqual((Payment.objects.count(), Payment.objects.filter(active=True).count()), (2, 1))

    def test_paid_marks_never_change_results(self):
        before = list(PlayerResult.objects.order_by("id").values_list("net", flat=True))
        services.mark_paid(self.game_night.pk, self.host, self.b_to_a.pk, uuid.uuid4())
        self.assertEqual(list(PlayerResult.objects.order_by("id").values_list("net", flat=True)), before)
        self.assertEqual(self.night.refresh().state, "finalized")

    def test_only_a_host_and_only_this_sessions_transfers(self):
        player = add_player(self.night.group, "ben")
        with self.assertRaises(NotAllowed):
            services.mark_paid(self.game_night.pk, player, self.b_to_a.pk, uuid.uuid4())
        other = worked_example()
        services.finalize(other.session.pk, other.host)
        with self.assertRaisesMessage(RuleError, "only after the session is closed"):
            services.mark_paid(other.session.night_id, other.host, self.b_to_a.pk, uuid.uuid4())
        services.close_night(other.session.night_id, other.host)
        with self.assertRaises(RuleError):
            services.mark_paid(other.session.night_id, other.host, self.b_to_a.pk, uuid.uuid4())
        with self.assertRaises(RuleError):
            services.mark_paid(self.game_night.pk, other.host, self.b_to_a.pk, uuid.uuid4())
        self.assertEqual(Payment.objects.count(), 0)

    def test_night_with_no_transfers_is_settled(self):
        even = worked_example((1000, 1000, 500))
        services.finalize(even.session.pk, even.host)
        services.close_night(even.session.night_id, even.host)
        self.assertEqual(queries.night_outcome(even.session.night).status, "settled")

    def test_marks_are_refused_before_the_session_is_closed(self):
        open_night = worked_example()
        services.finalize(open_night.session.pk, open_night.host)
        with self.assertRaises(RuleError):
            services.mark_unpaid(open_night.session.night_id, open_night.host, self.b_to_a.pk)


class PaidMarkViewTests(TestCase):
    def setUp(self):
        self.night = worked_example()
        services.finalize(self.night.session.pk, self.night.host)
        self.night_id = self.night.session.night_id
        services.close_night(self.night_id, self.night.host)
        self.transfer = Transfer.objects.order_by("position").first()
        self.page_url = reverse("night", args=[self.night_id])

    def test_host_marks_paid_and_undoes(self):
        self.client.force_login(self.night.host.user)
        self.assertContains(self.client.get(self.page_url), "Unsettled")
        page = self.client.post(reverse("transfer_paid", args=[self.night_id, self.transfer.pk]), follow=True)
        self.assertContains(page, "Partly settled")
        self.assertContains(page, "Not paid")  # the other transfer
        self.assertContains(page, "Paid ·")
        page = self.client.post(reverse("transfer_unpaid", args=[self.night_id, self.transfer.pk]), follow=True)
        self.assertContains(page, "Unsettled")

    def test_player_sees_marks_but_cannot_change_them(self):
        ben = add_player(self.night.group, "ben")
        self.client.force_login(ben.user)
        page = self.client.get(self.page_url)
        self.assertContains(page, "Not paid")
        self.assertNotContains(page, "Mark paid")
        for name in ("transfer_paid", "transfer_unpaid"):
            self.assertEqual(self.client.post(reverse(name, args=[self.night_id, self.transfer.pk])).status_code, 403)
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.post(reverse("transfer_paid", args=[self.night_id, self.transfer.pk])).status_code, 404)
        self.assertEqual(Payment.objects.count(), 0)
