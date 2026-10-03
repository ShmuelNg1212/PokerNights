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
        self.night = night = worked_example((16000, 7000, 2500))
        cash_out = night.cash("C", 400)
        ledger.reverse_cash_out(night.session.pk, night.host, cash_out.pk, "counted twice")
        override(night, name="A", note="chips from another set")
        settlement.finalize(night.session.pk, night.host)
        settlement.mark_paid(night.session.pk, night.host, Transfer.objects.first().pk, uuid.uuid4())
        self.url = reverse("session_log", args=[night.session.pk])
        self.member = add_player(night.group, "ben")

    def test_member_sees_the_full_record(self):
        self.client.force_login(self.member.user)
        page = self.client.get(self.url)
        expected = [
            "1. A", "2. B", "3. C",  # players in join order
            "Version 1", "₱1,000 = 10,000 chips",  # settings
            "₱500 · 5,000 chips",  # a buy-in with amount and chips
            "counted twice",  # the reversed cash-out keeps its reason
            "chips from another set",  # the override note
            "revision 1", "+₱550", "−₱300", "−₱250",  # results
            "B pays A", "paid",  # transfers and the paid mark
            "Finalized: ₱2,500 bought in", "Marked paid", "Ended play",  # audit trail
            "hana",  # who did it
        ]
        for text in expected:
            self.assertContains(page, text)

    def test_session_page_links_to_the_log_and_group_lists_past_games(self):
        self.client.force_login(self.member.user)
        self.assertContains(self.client.get(reverse("session", args=[self.night.session.pk])), self.url)
        group_page = self.client.get(reverse("group", args=[self.night.group.pk]))
        self.assertContains(group_page, "Past games")
        self.assertContains(group_page, reverse("session", args=[self.night.session.pk]))

    def test_non_member_gets_404(self):
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.get(self.url).status_code, 404)
