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
        self.b_to_a, self.c_to_a = Transfer.objects.order_by("position")

    def status(self):
        return queries.outcome(self.session).status

    def test_status_moves_from_unsettled_to_partly_to_settled(self):
        self.assertEqual(self.status(), "unsettled")
        payment = services.mark_paid(self.session.pk, self.host, self.b_to_a.pk, uuid.uuid4())
        self.assertEqual((payment.payer, payment.payee, payment.amount_centavos), (self.night.players["B"], self.night.players["A"], 30000))
        self.assertEqual(self.status(), "partly")
        outcome = queries.outcome(self.session)
        self.assertTrue(outcome.transfers[0].paid)
        self.assertIsNone(outcome.transfers[1].paid)  # the unpaid transfer stays visible
        services.mark_paid(self.session.pk, self.host, self.c_to_a.pk, uuid.uuid4())
        self.assertEqual(self.status(), "settled")

    def test_marking_twice_records_one_payment(self):
        request_id = uuid.uuid4()
        first = services.mark_paid(self.session.pk, self.host, self.b_to_a.pk, request_id)
        self.assertEqual(services.mark_paid(self.session.pk, self.host, self.b_to_a.pk, request_id).pk, first.pk)
        self.assertEqual(services.mark_paid(self.session.pk, self.host, self.b_to_a.pk, uuid.uuid4()).pk, first.pk)
        self.assertEqual(Payment.objects.count(), 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Payment.objects.create(
                session=self.session, payer=first.payer, payee=first.payee, amount_centavos=1, transfer=self.b_to_a,
                request_id=uuid.uuid4(), recorded_by=self.host.user,
            )

    def test_undo_keeps_the_record_and_allows_marking_again(self):
        services.mark_paid(self.session.pk, self.host, self.b_to_a.pk, uuid.uuid4())
        services.mark_unpaid(self.session.pk, self.host, self.b_to_a.pk, "wrong row")
        services.mark_unpaid(self.session.pk, self.host, self.b_to_a.pk)  # nothing to undo
        self.assertEqual(self.status(), "unsettled")
        self.assertEqual((Payment.objects.count(), PaymentReversal.objects.count()), (1, 1))
        services.mark_paid(self.session.pk, self.host, self.b_to_a.pk, uuid.uuid4())
        self.assertEqual((Payment.objects.count(), Payment.objects.filter(active=True).count()), (2, 1))

    def test_paid_marks_never_change_results(self):
        before = list(PlayerResult.objects.order_by("id").values_list("net_centavos", flat=True))
        services.mark_paid(self.session.pk, self.host, self.b_to_a.pk, uuid.uuid4())
        self.assertEqual(list(PlayerResult.objects.order_by("id").values_list("net_centavos", flat=True)), before)
        self.assertEqual(self.night.refresh().state, "finalized")

    def test_only_a_host_and_only_this_sessions_transfers(self):
        player = add_player(self.night.group, "ben")
        with self.assertRaises(NotAllowed):
            services.mark_paid(self.session.pk, player, self.b_to_a.pk, uuid.uuid4())
        other = worked_example()
        services.finalize(other.session.pk, other.host)
        with self.assertRaises(RuleError):
            services.mark_paid(other.session.pk, other.host, self.b_to_a.pk, uuid.uuid4())
        with self.assertRaises(RuleError):
            services.mark_paid(self.session.pk, other.host, self.b_to_a.pk, uuid.uuid4())
        self.assertEqual(Payment.objects.count(), 0)

    def test_night_with_no_transfers_is_settled(self):
        even = worked_example((10000, 10000, 5000))
        services.finalize(even.session.pk, even.host)
        self.assertEqual(queries.outcome(even.session).status, "settled")

    def test_each_mark_bumps_the_version_for_live_screens(self):
        version = self.night.refresh().version
        services.mark_paid(self.session.pk, self.host, self.b_to_a.pk, uuid.uuid4())
        services.mark_unpaid(self.session.pk, self.host, self.b_to_a.pk)
        self.assertEqual(self.night.refresh().version, version + 2)


class PaidMarkViewTests(TestCase):
    def setUp(self):
        self.night = worked_example()
        services.finalize(self.night.session.pk, self.night.host)
        self.transfer = Transfer.objects.order_by("position").first()
        self.page_url = reverse("session", args=[self.night.session.pk])

    def test_host_marks_paid_and_undoes(self):
        self.client.force_login(self.night.host.user)
        self.assertContains(self.client.get(self.page_url), "Unsettled")
        page = self.client.post(reverse("transfer_paid", args=[self.night.session.pk, self.transfer.pk]), follow=True)
        self.assertContains(page, "Partly settled")
        self.assertContains(page, "Not paid")  # the other transfer
        self.assertContains(page, "Paid ·")
        page = self.client.post(reverse("transfer_unpaid", args=[self.night.session.pk, self.transfer.pk]), follow=True)
        self.assertContains(page, "Unsettled")

    def test_player_sees_marks_but_cannot_change_them(self):
        ben = add_player(self.night.group, "ben")
        self.client.force_login(ben.user)
        page = self.client.get(self.page_url)
        self.assertContains(page, "Not paid")
        self.assertNotContains(page, "Mark paid")
        for name in ("transfer_paid", "transfer_unpaid"):
            self.assertEqual(self.client.post(reverse(name, args=[self.night.session.pk, self.transfer.pk])).status_code, 403)
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.post(reverse("transfer_paid", args=[self.night.session.pk, self.transfer.pk])).status_code, 404)
        self.assertEqual(Payment.objects.count(), 0)
