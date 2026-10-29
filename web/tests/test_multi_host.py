"""Two hosts at one set: what each one's count-up page shows of the other's counts."""

import uuid

from django.test import TestCase

from groups.models import Member
from groups.tests.helpers import add_player
from ledger import services as ledger
from ledger.tests.helpers import Night


class OtherHostCountTests(TestCase):
    def test_a_count_by_another_host_names_them_and_my_own_does_not(self):
        n2 = Night("A", "B")
        n2.buy("A", 1000); n2.buy("B", 1000)
        n2.go("reconciliation")
        ivy = add_player(n2.group, "Ivy", role=Member.Role.HOST)
        ledger.confirm_count(n2.session.pk, ivy, n2.players["A"].pk, 120000, uuid.uuid4())
        ledger.confirm_count(n2.session.pk, n2.host, n2.players["B"].pk, 80000, uuid.uuid4())
        self.client.force_login(n2.host.user)
        page = self.client.get(f"/s/{n2.session.pk}/").content.decode()
        a, b = n2.players["A"].pk, n2.players["B"].pk
        field = lambda pk: page.split(f'id="count-{pk}"')[0].rsplit("<input", 1)[1]
        self.assertIn('data-saved-by="Ivy"', field(a))
        self.assertIn('data-saved-shown="₱1,200"', field(a))
        self.assertNotIn("data-saved-by", field(b))
        self.assertIn(f'id="count-clash-{a}"', page)
