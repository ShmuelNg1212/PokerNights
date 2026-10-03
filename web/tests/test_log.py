import uuid

from django.test import TestCase
from django.urls import reverse

from groups.tests.helpers import add_player, make_user
from ledger import services as ledger
from ledger.tests.test_balance import override, worked_example
from settlement import services as settlement
from settlement.models import Transfer


class SessionLogTests(TestCase):
    def setUp(self):
        self.night = night = worked_example((1600, 700, 250))
        cash_out = night.cash("C", 40)
        ledger.reverse_cash_out(night.session.pk, night.host, cash_out.pk, "counted twice")
        override(night, name="A", note="A was overpaid")
        settlement.finalize(night.session.pk, night.host)
        settlement.close_night(night.session.night_id, night.host)
        settlement.mark_paid(night.session.night_id, night.host, Transfer.objects.first().pk, uuid.uuid4())
        self.url = reverse("session_log", args=[night.session.pk])
        self.member = add_player(night.group, "ben")

    def test_member_sees_the_full_record(self):
        self.client.force_login(self.member.user)
        page = self.client.get(self.url)
        expected = [
            "1. A", "2. B", "3. C",  # players in join order
            "Version 1", "usually ₱1,000",  # settings
            "₱500",  # a buy-in with its amount
            "counted twice",  # the reversed cash-out keeps its reason
            "A was overpaid",  # the override note
            "revision 1", "+₱550", "−₱300", "−₱250",  # results
            "Finalized set 1: ₱2,500 bought in", "Closed the session", "Marked paid", "Ended play",  # audit trail
            "hana",  # who did it
        ]
        for text in expected:
            self.assertContains(page, text)
        self.assertNotContains(page, "chips")

    def test_session_page_links_to_the_log_and_group_lists_past_games(self):
        self.client.force_login(self.member.user)
        self.assertContains(self.client.get(reverse("session", args=[self.night.session.pk])), self.url)
        group_page = self.client.get(reverse("group", args=[self.night.group.pk]))
        self.assertContains(group_page, reverse("night", args=[self.night.session.night_id]))
        night_page = self.client.get(reverse("night", args=[self.night.session.night_id]))
        self.assertContains(night_page, reverse("session", args=[self.night.session.pk]))

    def test_transfers_and_payment_records_are_on_the_session_page(self):
        self.client.force_login(self.member.user)
        page = self.client.get(reverse("night", args=[self.night.session.night_id]))
        for text in ("<strong>B</strong> pays <strong>A</strong>", "Paid ·", "Payment records", "B → A ₱300"):
            self.assertContains(page, text)

    def test_non_member_gets_404(self):
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.get(self.url).status_code, 404)
