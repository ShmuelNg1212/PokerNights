"""The results a member sends to the group chat: the card's data and the text, from the closed session's own figures."""

import json
import re
import uuid

from django.test import TestCase, override_settings
from django.urls import reverse

from games import services as games
from games.models import GameNight
from ledger.tests.helpers import Night
from settlement import queries, services
from settlement.tests.test_night import TwoSets
from web import share


def closed(night, figures):
    """Play one set to the end and close the session. ``figures`` maps a name to (buy-in, cash-out)."""
    for name, (buy_in, _) in figures.items():
        night.buy(name, buy_in)
    night.go("reconciliation")
    for name, (_, cash_out) in figures.items():
        night.cash(name, cash_out)
    services.finalize(night.session.pk, night.host)
    services.close_night(night.session.night_id, night.host)
    return GameNight.objects.get(pk=night.session.night_id)


def card_of(night):
    outcome = queries.night_outcome(night)
    return share.card(night, outcome, queries.night_recap(night, outcome.standings, results=outcome.results))


class ShareCardTests(TestCase):
    def test_text_of_a_session_of_two_sets(self):
        two = TwoSets()
        services.close_night(two.night_id, two.host)
        card = card_of(GameNight.objects.get(pk=two.night_id))
        lines = card["text"].split("\n")
        self.assertEqual(lines[:5], ["Friday table · Fri, Oct 9", "Results", "1. A +₱200", "2. B +₱100", "3. C −₱300"])
        self.assertEqual(lines[5], "Who pays whom")
        self.assertEqual(sorted(lines[6:8]), ["C → A ₱200", "C → B ₱100"])
        self.assertEqual(lines[8:], ["PokerNights"])

    def test_rows_and_transfers_are_the_session_pages(self):
        two = TwoSets()
        services.close_night(two.night_id, two.host)
        night = GameNight.objects.get(pk=two.night_id)
        card, outcome = card_of(night), queries.night_outcome(night)
        self.assertEqual((card["title"], card["when"]), ("Friday table", "Fri, Oct 9 · Miguel's place"))
        self.assertEqual(card["facts"], "3 players · 2 sets · ₱5,000 bought in")
        self.assertEqual(
            [(r["place"], r["name"], r["amount"], r["sign"], r["share"]) for r in card["rows"]],
            [(1, "A", "+₱200", "plus", 66), (2, "B", "+₱100", "plus", 33), (3, "C", "−₱300", "minus", 100)],
        )
        self.assertEqual([(r["chip"], r["k"]) for r in card["rows"]], [("A", 1), ("B", 2), ("C", 3)])
        self.assertEqual(
            [(t["payer"]["name"], t["payee"]["name"], t["amount"]) for t in card["transfers"]],
            [(t.payer.display_name, t.payee.display_name, f"₱{t.amount // 100:,}") for t in outcome.transfers],
        )
        self.assertRegex(card["foot"][0], r"^Closed [A-Z][a-z]{2} \d{1,2}, \d{1,2}:\d{2} [AP]M$")
        self.assertEqual(len(card["foot"]), 1)
        self.assertEqual(card["file"], "pokernights-friday-table-2026-10-09.png")

    def test_ties_share_a_place_and_a_zero_is_even(self):
        night = closed(Night("A", "B", "C", "D"), {"A": (1000, 1600), "B": (1000, 700), "C": (1000, 700), "D": (500, 500)})
        card = card_of(night)
        self.assertEqual(
            [(r["place"], r["name"], r["amount"], r["sign"]) for r in card["rows"]],
            [(1, "A", "+₱600", "plus"), (2, "D", "₱0", "even"), (3, "B", "−₱300", "minus"), (3, "C", "−₱300", "minus")],
        )
        self.assertIn("3. B −₱300\n3. C −₱300", card["text"])

    def test_nobody_owes(self):
        card = card_of(closed(Night("A", "B"), {"A": (1000, 1000), "B": (500, 500)}))
        self.assertEqual(card["transfers"], [])
        self.assertIn("Who pays whom\nNobody owes anything.\nPokerNights", card["text"])

    def test_chips_game(self):
        card = card_of(closed(Night("A", "B", unit="chips"), {"A": (1000, 1500), "B": (1000, 500)}))
        self.assertEqual([r["amount"] for r in card["rows"]], ["+500 chips", "−500 chips"])
        self.assertEqual(card["facts"], "2 players · 1 set · 2,000 chips bought in")
        self.assertIn("B → A 500 chips", card["text"])

    def test_rake_is_said_only_when_collected(self):
        night = closed(Night("A", "B"), {"A": (1000, 1500), "B": (1000, 500)})
        outcome = queries.night_outcome(night)
        recap = queries.night_recap(night, outcome.standings, results=outcome.results)
        recap.total_rake = 5000
        self.assertEqual(share.card(night, outcome, recap)["foot"][1], "Results are after rake.")

    def test_a_name_cannot_break_the_file_name(self):
        night = Night("A", "B")
        night.session.table.name = "Ñino's / Table #2"
        night.session.table.save()
        self.assertEqual(card_of(closed(night, {"A": (1000, 1500), "B": (1000, 500)}))["file"], "pokernights-ninos-table-2-2026-10-09.png")


class SharePageTests(TestCase):
    def setUp(self):
        self.game = Night("A", "B")
        self.url = reverse("night", args=[self.game.session.night_id])
        self.client.force_login(self.game.host.user)

    def close(self):
        return closed(self.game, {"A": (1000, 1500), "B": (1000, 500)})

    def test_a_closed_session_carries_the_card_and_the_text(self):
        night = self.close()
        html = self.client.get(self.url).content.decode()
        data = json.loads(re.search(r'<script id="share-card" type="application/json">(.*?)</script>', html, re.S).group(1))
        self.assertEqual(data, json.loads(json.dumps(card_of(night))))
        self.assertIn('data-sheet-open="share"', html)
        self.assertIn("Share results", html)
        # Without JavaScript the text is in the page, to select and copy by hand.
        self.assertIn("1. A +₱500\n2. B −₱500", html)

    def test_any_member_can_share(self):
        from groups.tests.helpers import add_player

        self.close()
        self.client.force_login(add_player(self.game.group, "Player").user)
        self.assertContains(self.client.get(self.url), 'data-sheet-open="share"')

    def test_no_control_on_an_open_or_archived_session(self):
        self.assertNotContains(self.client.get(self.url), "share-card")
        self.close()
        games.archive_night(self.game.session.night_id, self.game.host)
        self.assertNotContains(self.client.get(self.url), "share-card")

    @override_settings(SHARE_RESULTS=False)
    def test_switch_off(self):
        self.close()
        page = self.client.get(self.url)
        self.assertNotContains(page, "share-card")
        self.assertNotContains(page, "Share results")
