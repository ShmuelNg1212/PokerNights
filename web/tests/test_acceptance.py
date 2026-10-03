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
from ledger.models import BuyIn, PlayerResult
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


class EndOfSetAcceptanceTest(TestCase):
    """Six players. Play ends at 11:00 PM. Four are counted by 11:10, one at zero. Then the other two."""

    def test_counting_takes_time_but_adds_no_playing_time(self):
        import datetime
        from unittest import mock

        from games import clock
        from ledger.models import CashOut, Finalization

        start = datetime.datetime(2026, 10, 9, 12, 0, tzinfo=datetime.timezone.utc)  # 8:00 PM in Manila

        def at(minutes):
            return mock.patch("games.services.timezone.now", return_value=start + datetime.timedelta(minutes=minutes))

        host = sign_up("hana")
        host.post(reverse("group_create"), {"name": "Friday Game"})
        group = GameGroup.objects.get()
        host.post(reverse("table_create", args=[group.pk]), {"name": "Friday table", "seat_count": "9"})
        for name in "ABCDEF":
            host.post(reverse("member_add", args=[group.pk]), {"name": name})
        host.post(reverse("session_create", args=[group.pk]), {
            "table_id": group.tables.get().pk, "game_date": "2026-10-09", "game_type": "nlh", "unit": "php",
            "small_blind": "10", "big_blind": "20", "min_buy_in": "500", "max_buy_in": "5000", "default_buy_in": "1000",
        })
        game = GameSession.objects.get()
        host.post(reverse("session_transition", args=[game.pk]), {"action": "open"})
        ids = [m.pk for m in Member.objects.filter(group=group, user__isnull=True)]
        host.post(reverse("participants_add", args=[game.pk]), {"member_id": ids})
        seats = {p.member.display_name: p for p in Participant.objects.filter(session=game)}
        for name in "ABCDEF":
            host.post(reverse("buy_in_add", args=[game.pk]), {"participant_id": seats[name].pk, "amount": "1000"})
        with at(0):
            host.post(reverse("session_transition", args=[game.pk]), {"action": "start"})
        with at(180):  # 11:00 PM
            host.post(reverse("session_transition", args=[game.pk]), {"action": "end"})

        page_url = reverse("session", args=[game.pk])
        page = host.get(page_url)
        self.assertContains(page, "Play ended 11:00 PM")
        self.assertContains(page, "3 h 00 min")
        self.assertContains(page, "Cash out counted players (0)")
        self.assertContains(page, "6 awaiting count")

        # 11:10 PM: four players are counted, C with nothing left.
        confirm = reverse("count_confirm", args=[game.pk])
        for name, amount in (("A", "2500"), ("B", "1500"), ("C", "0"), ("D", "800")):
            host.post(confirm, {"participant_id": seats[name].pk, "amount": amount})
        page = host.get(page_url)
        self.assertContains(page, "Cash out counted players (4)")
        self.assertContains(page, "Still to count: E, F.")

        review_url = reverse("cash_out_counted", args=[game.pk])
        review = host.get(review_url)
        for text in ("₱2,500", "₱1,500", "₱0", "₱800", "₱4,800", "Cash out 4 players"):
            self.assertContains(review, text)
        count_ids = re.findall(r'name="count_id" value="(\d+)"', review.content.decode())
        self.assertEqual(len(count_ids), 4)
        done = host.post(review_url, {"count_id": count_ids}, follow=True)
        self.assertContains(done, "4 players cashed out; 2 awaiting final counts.")
        self.assertEqual(CashOut.objects.filter(kind="final").count(), 4)
        self.assertEqual((GameSession.objects.get().state, Finalization.objects.count()), ("reconciliation", 0))

        # Finalizing now is refused: two players are not cashed out.
        refused = host.post(reverse("session_finalize", args=[game.pk]), follow=True)
        self.assertContains(refused, "Not cashed out yet: E, F")

        # Later: the other two are counted and cashed out with the same action.
        for name, amount in (("E", "700"), ("F", "500")):
            host.post(confirm, {"participant_id": seats[name].pk, "amount": amount})
        review = host.get(review_url)
        count_ids = re.findall(r'name="count_id" value="(\d+)"', review.content.decode())
        done = host.post(review_url, {"count_id": count_ids}, follow=True)
        self.assertContains(done, "2 players cashed out; everyone is cashed out.")
        self.assertContains(done, "The books balance")

        # However long counting took, each player played three hours.
        late = start + datetime.timedelta(minutes=260)
        self.assertEqual(set(clock.player_seconds(game, late).values()), {180 * 60})
        self.assertEqual(clock.set_seconds(game, late), 180 * 60)
        host.post(reverse("session_finalize", args=[game.pk]))
        self.assertEqual(set(PlayerResult.objects.values_list("play_seconds", flat=True)), {180 * 60})
        log = host.get(reverse("session_log", args=[game.pk]))
        for text in ("Play from", "Confirmed C&#x27;s final count: ₱0", "Cashed out 4 counted players: A, B, C, D", "Cashed out 2 counted players: E, F"):
            self.assertContains(log, text)


class TwoSetSessionAcceptanceTest(TestCase):
    """Set 1: A wins ₱600 from B and C. Set 2: B wins ₱400 from A. One settle-up for the session."""

    def play_set(self, host, game, figures):
        seats = {p.member.display_name: p for p in Participant.objects.filter(session=game)}
        for name, (buy_in, _) in figures.items():
            host.post(reverse("buy_in_add", args=[game.pk]), {"participant_id": seats[name].pk, "amount": str(buy_in)})
        host.post(reverse("session_transition", args=[game.pk]), {"action": "start"})
        host.post(reverse("session_transition", args=[game.pk]), {"action": "end"})
        for name, (_, final) in figures.items():
            host.post(reverse("count_confirm", args=[game.pk]), {"participant_id": seats[name].pk, "amount": str(final)})
        review_url = reverse("cash_out_counted", args=[game.pk])
        count_ids = re.findall(r'name="count_id" value="(\d+)"', host.get(review_url).content.decode())
        host.post(review_url, {"count_id": count_ids})
        return host.post(reverse("session_finalize", args=[game.pk]), follow=True)

    def test_two_sets_one_settle_up(self):
        host = sign_up("hana")
        host.post(reverse("group_create"), {"name": "Friday Game"})
        group = GameGroup.objects.get()
        host.post(reverse("table_create", args=[group.pk]), {"name": "Friday table", "seat_count": "9"})
        for name in "ABC":
            host.post(reverse("member_add", args=[group.pk]), {"name": name})
        host.post(reverse("session_create", args=[group.pk]), {
            "table_id": group.tables.get().pk, "game_date": "2026-10-09", "game_type": "nlh", "unit": "php",
            "small_blind": "10", "big_blind": "20", "min_buy_in": "500", "max_buy_in": "2000", "default_buy_in": "1000",
        })
        first = GameSession.objects.get()
        night_url = reverse("night", args=[first.night_id])
        host.post(reverse("session_transition", args=[first.pk]), {"action": "open"})
        host.post(reverse("participants_add", args=[first.pk]), {"member_id": [m.pk for m in Member.objects.filter(group=group, user__isnull=True)]})

        result = self.play_set(host, first, {"A": (1000, 1600), "B": (1000, 700), "C": (500, 200)})
        self.assertContains(result, "Results of set 1")
        self.assertNotContains(result, "pays <strong>")
        self.assertEqual(Transfer.objects.count(), 0)

        # The next set: same table and players, fresh buy-ins, its own timer.
        opened = host.post(reverse("next_set", args=[first.night_id]), follow=True)
        second = GameSession.objects.get(set_number=2)
        self.assertContains(opened, "Set 2 is open")
        self.assertEqual(sorted(second.participants.values_list("member__display_name", flat=True)), ["A", "B", "C"])
        self.assertContains(opened, "₱0")  # nothing bought in yet
        self.assertContains(host.get(night_url), "Not done: set 2 (open)")

        self.play_set(host, second, {"A": (1000, 600), "B": (1000, 1400), "C": (500, 500)})
        night_page = host.get(night_url)
        for text in ("Results so far", "+₱200", "+₱100", "−₱300", "Close session and settle up"):
            self.assertContains(night_page, text)

        closed = host.post(reverse("night_close", args=[first.night_id]), follow=True)
        for text in ("<strong>C</strong> pays <strong>A</strong>", "₱200", "<strong>C</strong> pays <strong>B</strong>", "₱100", "Session closed"):
            self.assertContains(closed, text)
        self.assertEqual(
            [(t.payer.display_name, t.payee.display_name, t.amount) for t in Transfer.objects.order_by("position")],
            [("C", "A", 20000), ("C", "B", 10000)],
        )
        self.assertNotContains(closed, "Start next set")
