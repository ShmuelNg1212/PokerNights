"""A player's "Your count" card says where their count is: counted, confirmed, cashed out."""

import re
import uuid

from django.test import TestCase
from django.urls import reverse

from ledger import services as ledger
from ledger.tests.test_player_entries import night_with_logins


class OwnCountStageTests(TestCase):
    def setUp(self):
        self.night = night_with_logins("reconciliation")
        self.sid = self.night.session.pk
        self.maria = self.night.players["maria"]
        self.client.force_login(self.night.maria.user)

    def card(self):
        html = self.client.get(reverse("session", args=[self.sid])).content.decode()
        card = html[html.index('class="own-count'):]
        card = card[:card.index("</section>")]
        states = re.findall(r'<li data-state="(\w+)"( data-fresh data-status="\w+")?( data-wait)?>', card)
        stage = re.search(r'data-stage="(\w+)" data-watch="own-count" data-value="([^"]*)"', card)
        return stage.groups(), [(s, bool(fresh), bool(wait)) for s, fresh, wait in states], card

    def test_the_steps_follow_the_count(self):
        stage, steps, card = self.card()
        self.assertEqual(stage, ("open", "open:"))
        self.assertEqual(steps, [("now", False, False), ("todo", False, False), ("todo", False, False)])
        self.assertIn("Step 1 of 3: send your count.", card)
        self.assertNotIn("<svg", card[:card.index("</ol>")])

        ledger.enter_count(self.sid, self.night.maria, 145000, uuid.uuid4())
        stage, steps, card = self.card()
        self.assertEqual(stage, ("sent", "sent:145000"))
        self.assertEqual(steps, [("done", True, False), ("now", False, True), ("todo", False, False)])
        self.assertIn("waiting for the host to confirm", card)

        ledger.confirm_count(self.sid, self.night.host, self.maria.pk, 140000, uuid.uuid4())
        stage, steps, card = self.card()
        self.assertEqual(stage, ("confirmed", "confirmed:140000"))
        self.assertEqual(steps, [("done", False, False), ("done", True, False), ("now", False, True)])

        ledger.record_cash_out(self.sid, self.night.host, self.maria.pk, 140000, uuid.uuid4())
        stage, steps, card = self.card()
        self.assertEqual(stage, ("cashed", "cashed:140000"))
        self.assertEqual(steps, [("done", False, False), ("done", False, False), ("done", True, False)])
        self.assertIn("All 3 steps done", card)

    def test_a_count_the_host_typed_counts_as_counted(self):
        ledger.confirm_count(self.sid, self.night.host, self.maria.pk, 90000, uuid.uuid4())
        stage, steps, _ = self.card()
        self.assertEqual(stage, ("confirmed", "confirmed:90000"))
        self.assertEqual([s for s, _, _ in steps], ["done", "done", "now"])
