"""Adding several players touches the roster only: no money, and connected screens update."""

import uuid

from django.test import TestCase
from django.urls import reverse

from games import services as games
from games.tests.test_add_players import NAMES, Roster
from ledger import queries
from ledger.models import BuyIn, CashOut, PlayerResult
from settlement.models import Payment


class AddPlayersSideEffectTests(TestCase):
    def test_no_money_record_is_created(self):
        roster = Roster(state="running")
        roster.add()
        self.assertEqual(
            (BuyIn.objects.count(), CashOut.objects.count(), Payment.objects.count(), PlayerResult.objects.count()),
            (0, 0, 0, 0),
        )
        self.assertFalse(games.has_money(roster.session))
        summary = queries.summary(roster.session)
        self.assertEqual((summary.player_count, summary.buy_in_count, summary.total), (4, 0, 0))

    def test_existing_money_and_players_are_untouched(self):
        from ledger.tests.helpers import Night

        night = Night("Earl")
        night.buy("Earl", 1000)
        before = queries.summary(night.session)
        from groups import services as groups

        ids = [groups.add_roster_player(night.host, name).pk for name in NAMES]
        games.add_participants(night.session.pk, night.host, ids, uuid.uuid4())
        after = queries.summary(night.session)
        self.assertEqual((after.total, after.buy_in_count), (before.total, before.buy_in_count))
        self.assertEqual(after.lines[0].participant.member.display_name, "Earl")
        self.assertEqual(after.lines[0].participant.join_order, 1)
        self.assertEqual(after.player_count, 5)

    def test_connected_screens_get_the_new_roster(self):
        roster = Roster()
        viewer = roster.members["Ana"].user
        self.client.force_login(viewer)
        state_url = reverse("session_state", args=[roster.session.pk])
        seen = self.client.get(state_url).json()["version"]
        self.assertEqual(self.client.get(state_url, {"v": seen}).status_code, 204)
        roster.add("Ben", "Carlo", "Dani")
        snapshot = self.client.get(state_url, {"v": seen}).json()
        self.assertEqual(snapshot["version"], seen + 1)
        for name in ("Ben", "Carlo", "Dani"):
            self.assertIn(name, snapshot["html"])
