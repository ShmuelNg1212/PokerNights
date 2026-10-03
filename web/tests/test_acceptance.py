"""The worked example from SPEC.md and the study, driven through the pages like a user.

A buys in for ₱1,000 and finishes with ₱1,600. B buys in for ₱1,000 and
finishes with ₱700. C buys in for ₱500 and finishes with ₱200. With no prior
payments, B pays A ₱300 and C pays A ₱300.
"""

import re

from django.test import Client, TestCase
from django.urls import reverse

from games.models import GameSession, Participant
from groups.models import GameGroup, Member
from ledger.models import BuyIn
from settlement.models import Transfer

PASSWORD = "tablestakes-91"


def sign_up(name):
    client = Client()
    response = client.post(reverse("signup"), {"username": name, "password1": PASSWORD, "password2": PASSWORD})
    assert response.status_code == 302, response.content
    return client


class GameNightAcceptanceTest(TestCase):
    def test_from_sign_up_to_settled(self):
        # --- The host signs up, creates a group, a preset and a table.
        host = sign_up("hana")
        host.post(reverse("group_create"), {"name": "Friday Game"})
        group = GameGroup.objects.get()
        host.post(reverse("preset_create", args=[group.pk]), {
            "name": "10/20", "game_type": "nlh", "small_blind": "10", "big_blind": "20",
            "min_buy_in": "500", "max_buy_in": "2000", "default_buy_in": "1000",
        })
        host.post(reverse("table_create", args=[group.pk]), {"name": "Friday table", "seat_count": "9"})

        # --- Players: B signs up through the invite link; A and C are roster players without logins.
        host.post(reverse("invite_create", args=[group.pk]))
        link = re.search(r"/join/[\w-]+/", host.get(reverse("group", args=[group.pk])).content.decode()).group(0)
        player_b = sign_up("B")
        self.assertContains(player_b.post(link, follow=True), "Friday Game")
        host.post(reverse("member_add", args=[group.pk]), {"name": "A"})
        host.post(reverse("member_add", args=[group.pk]), {"name": "C"})

        # --- A stranger sees nothing.
        stranger = sign_up("stranger")
        self.assertEqual(stranger.get(reverse("group", args=[group.pk])).status_code, 404)

        # --- The host creates the game and opens it.
        table_id = group.tables.get().pk
        host.post(reverse("session_create", args=[group.pk]), {
            "table_id": table_id, "game_date": "2026-10-09", "location": "Miguel's place", "game_type": "nlh",
            "small_blind": "10", "big_blind": "20", "min_buy_in": "500",
            "max_buy_in": "2000", "default_buy_in": "1000",
        })
        session = GameSession.objects.get()
        page_url = reverse("session", args=[session.pk])
        self.assertEqual(player_b.get(page_url).status_code, 404)  # still a draft
        host.post(reverse("session_transition", args=[session.pk]), {"action": "open"})

        # --- B joins from a phone (a double tap adds one entry). The host adds A and C.
        player_b.post(reverse("participant_add", args=[session.pk]))
        player_b.post(reverse("participant_add", args=[session.pk]))
        members = {m.display_name: m for m in Member.objects.filter(group=group)}
        host.post(reverse("participant_add", args=[session.pk]), {"member_id": members["A"].pk})
        host.post(reverse("participant_add", args=[session.pk]), {"member_id": members["C"].pk})
        seats = {p.member.display_name: p for p in Participant.objects.filter(session=session)}
        self.assertEqual(sorted(seats), ["A", "B", "C"])

        # --- Buy-ins, then the game starts.
        add_buy_in = reverse("buy_in_add", args=[session.pk])
        host.post(add_buy_in, {"participant_id": seats["A"].pk, "amount": "1000"})
        host.post(add_buy_in, {"participant_id": seats["B"].pk, "amount": "1000"})
        host.post(reverse("session_transition", args=[session.pk]), {"action": "start"})
        host.post(add_buy_in, {"participant_id": seats["C"].pk, "amount": "500"})  # C arrives late with a half buy-in
        self.assertEqual(player_b.post(add_buy_in, {"participant_id": seats["B"].pk, "amount": "1000"}).status_code, 403)

        live = player_b.get(page_url)
        self.assertContains(live, "Total bought in")
        self.assertContains(live, "₱2,500")
        self.assertContains(live, "Still in play")
        self.assertNotContains(live, "chips")  # a pesos game shows no chip figure
        self.assertEqual(stranger.get(reverse("session_state", args=[session.pk])).status_code, 404)

        # --- B's phone learns about a change through polling.
        version = GameSession.objects.get().version
        state_url = reverse("session_state", args=[session.pk])
        self.assertEqual(player_b.get(state_url, {"v": version}).status_code, 204)

        # --- B leaves early. Then play ends and the rest is counted.
        add_cash_out = reverse("cash_out_add", args=[session.pk])
        host.post(add_cash_out, {"participant_id": seats["B"].pk, "amount": "700", "left": "1"})
        snapshot = player_b.get(state_url, {"v": version}).json()
        self.assertIn("₱1,800", snapshot["html"])  # still in play
        host.post(reverse("session_transition", args=[session.pk]), {"action": "end"})
        host.post(add_cash_out, {"participant_id": seats["A"].pk, "amount": "1600"})

        # --- C is not counted yet: finalize is refused and says why.
        refused = host.post(reverse("session_finalize", args=[session.pk]), follow=True)
        self.assertContains(refused, "Not cashed out yet: C")
        host.post(add_cash_out, {"participant_id": seats["C"].pk, "amount": "250"})
        self.assertContains(host.get(page_url), "₱50 too much")
        wrong = session.cash_outs.get(participant=seats["C"])
        host.post(reverse("cash_out_reverse", args=[session.pk, wrong.pk]), {"reason": "miscounted"})
        host.post(add_cash_out, {"participant_id": seats["C"].pk, "amount": "200"})
        self.assertContains(host.get(page_url), "The books balance")

        # --- Finalize the set: results only. Then close the session: who pays whom.
        results = host.post(reverse("session_finalize", args=[session.pk]), follow=True)
        for text in ("+₱600", "−₱300", "Payment:</strong> at the end of the session"):
            self.assertContains(results, text)
        self.assertEqual(Transfer.objects.count(), 0)
        night_url = reverse("night", args=[session.night_id])
        closed = host.post(reverse("night_close", args=[session.night_id]), follow=True)
        for text in ("<strong>B</strong> pays <strong>A</strong>", "<strong>C</strong> pays <strong>A</strong>"):
            self.assertContains(closed, text)
        transfers = list(Transfer.objects.order_by("position"))
        self.assertEqual(
            [(t.payer.display_name, t.payee.display_name, t.amount) for t in transfers],
            [("B", "A", 30000), ("C", "A", 30000)],
        )
        mine = player_b.get(night_url)
        self.assertContains(mine, "Your result in this session")
        self.assertContains(mine, "You pay <strong>A</strong>")
        self.assertContains(mine, "Unsettled")

        # --- The game is closed to changes.
        host.post(add_buy_in, {"participant_id": seats["A"].pk, "amount": "1000"})
        self.assertEqual(BuyIn.objects.count(), 3)

        # --- Payments are marked one by one, on the session page.
        host.post(reverse("transfer_paid", args=[session.night_id, transfers[0].pk]))
        self.assertContains(player_b.get(night_url), "Partly settled")
        host.post(reverse("transfer_paid", args=[session.night_id, transfers[1].pk]))
        self.assertContains(player_b.get(night_url), "Settled")

        # --- The log shows the whole night, and the group lists the game as past.
        log = player_b.get(reverse("session_log", args=[session.pk]))
        for text in ("miscounted", "Finalized set 1: ₱2,500 bought in", "Marked paid", "B left the game"):
            self.assertContains(log, text)
        self.assertContains(player_b.get(reverse("group", args=[group.pk])), "Past sessions")


class ChipsGameAcceptanceTest(TestCase):
    """The same night counted in chips: no peso value appears anywhere."""

    def test_chips_game_through_the_pages(self):
        host = sign_up("hana")
        host.post(reverse("group_create"), {"name": "Play Money Night"})
        group = GameGroup.objects.get()
        host.post(reverse("table_create", args=[group.pk]), {"name": "Kitchen table", "seat_count": "6"})
        for name in "ABC":
            host.post(reverse("member_add", args=[group.pk]), {"name": name})
        host.post(reverse("session_create", args=[group.pk]), {
            "table_id": group.tables.get().pk, "game_date": "2026-10-09", "game_type": "nlh", "unit": "chips",
            "small_blind": "10", "big_blind": "20", "min_buy_in": "500", "max_buy_in": "2000", "default_buy_in": "1000",
        })
        session = GameSession.objects.get()
        self.assertEqual(session.unit, "chips")
        host.post(reverse("session_transition", args=[session.pk]), {"action": "open"})
        for member in Member.objects.filter(group=group, user__isnull=True):
            host.post(reverse("participant_add", args=[session.pk]), {"member_id": member.pk})
        seats = {p.member.display_name: p for p in Participant.objects.filter(session=session)}
        for name, chips in (("A", "1000"), ("B", "1000"), ("C", "500")):
            host.post(reverse("buy_in_add", args=[session.pk]), {"participant_id": seats[name].pk, "amount": chips})
        host.post(reverse("session_transition", args=[session.pk]), {"action": "start"})
        page_url = reverse("session", args=[session.pk])
        live = host.get(page_url)
        self.assertContains(live, "2,500 chips")
        self.assertContains(live, "Chips game")
        self.assertNotContains(live, "₱")

        host.post(reverse("session_transition", args=[session.pk]), {"action": "end"})
        for name, chips in (("A", "1600"), ("B", "700"), ("C", "200")):
            host.post(reverse("cash_out_add", args=[session.pk]), {"participant_id": seats[name].pk, "amount": chips})
        results = host.post(reverse("session_finalize", args=[session.pk]), follow=True)
        for text in ("+600 chips", "−300 chips"):
            self.assertContains(results, text)
        self.assertNotContains(results, "₱")
        closed = host.post(reverse("night_close", args=[session.night_id]), follow=True)
        for text in ("<strong>B</strong> pays <strong>A</strong>", "300 chips"):
            self.assertContains(closed, text)
        self.assertNotContains(closed, "₱")
        self.assertNotContains(host.get(reverse("session_log", args=[session.pk])), "₱")
        self.assertEqual(
            [(t.payer.display_name, t.payee.display_name, t.amount) for t in Transfer.objects.order_by("position")],
            [("B", "A", 300), ("C", "A", 300)],
        )
