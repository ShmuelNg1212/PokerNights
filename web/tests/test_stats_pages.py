"""The Stats tab and a player's page."""

import datetime

from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from groups import services as groups
from groups.tests.helpers import add_player, make_group, make_user
from settlement.tests.test_stats import Club

D = datetime.date
NIGHTS = [D(2026, 8, 6), D(2026, 8, 20), D(2026, 9, 3), D(2026, 9, 17), D(2026, 10, 1)]


class StatsPagesTests(TestCase):
    """Ana wins steadily, Ben loses, Carlo joined for the last night only."""

    @classmethod
    def setUpTestData(cls):
        cls.club = Club()
        for n, day in enumerate(NIGHTS):
            figures = {"Ana": (1000, 1400), "Ben": (1000, 600)}
            if n == 2:
                figures = {"Ana": (1000, 700), "Ben": (1000, 1300)}
            if n == 4:
                figures = {"Ana": (1000, 1500), "Ben": (2000, 1000), "Carlo": (1000, 1500)}
            cls.club.session(day, figures)
        cls.group, cls.host = cls.club.group, cls.club.host
        cls.ana, cls.ben, cls.carlo = (cls.club.member(n) for n in ("Ana", "Ben", "Carlo"))
        cls.viewer = add_player(cls.group, "viewer")

    def setUp(self):
        self.client.force_login(self.host.user)
        self.url = reverse("group", args=[self.group.pk])

    def stats(self, **params):
        return self.client.get(self.url, {"view": "stats", **params})

    def player(self, member, **params):
        return self.client.get(reverse("player", args=[self.group.pk, member.pk]), params)

    def names(self, page, key="stat_ranked"):
        return [line.record.member.display_name for line in page.context[key]]

    def test_board_ranks_and_sets_apart_players_under_the_minimum(self):
        page = self.stats()
        self.assertEqual(self.names(page), ["Ana", "Ben"])
        self.assertEqual(self.names(page, "stat_unranked"), ["Carlo"])
        self.assertContains(page, "Not ranked yet")
        self.assertContains(page, "3 sessions put a player on this board.")
        self.assertContains(page, "+₱1,400")      # Ana: 400 + 400 − 300 + 400 + 500
        self.assertContains(page, reverse("player", args=[self.group.pk, self.ana.pk]) + "?period=all&amp;unit=php")

    def test_each_sort_shows_its_figure(self):
        self.assertContains(self.stats(sort="average"), "+₱280")          # 1,400 over 5
        self.assertContains(self.stats(sort="return"), "+28%")            # 1,400 on 5,000 bought in
        page = self.stats(sort="sessions")
        self.assertEqual(page.context["stat_sort"], "sessions")
        self.assertNotContains(self.stats(), "sort=hour")                 # no recorded time, so not offered
        self.assertEqual(self.stats(sort="hour").context["stat_sort"], "profit")

    def test_periods_and_the_month_list(self):
        page = self.stats(period="2026-10")
        self.assertEqual(self.names(page), ["Ana", "Carlo", "Ben"])
        self.assertContains(page, "October 2026")
        self.assertEqual([slug for slug, _ in page.context["stat_months"]], ["2026-10", "2026-09", "2026-08"])
        self.assertEqual(self.stats(period="nonsense").context["stat_period"].slug, "all")
        self.assertContains(self.stats(period="2025-01"), "No closed session in January 2025")

    def test_chips_and_pesos_never_share_a_board_or_a_page(self):
        for day in NIGHTS[:3]:
            self.club.session(day, {"Ana": (1000, 400), "Ben": (1000, 1600)}, unit="chips")
        page = self.stats(unit="chips")
        self.assertContains(page, 'aria-label="Unit"')
        self.assertContains(page, "+1,800 chips")
        board = page.content.decode().split("data-stat-board>")[1].split("</ol>")[0]
        self.assertNotIn("₱", board)
        self.assertEqual(self.names(page), ["Ben", "Ana"])
        player = self.player(self.ana, unit="chips")
        self.assertNotIn("₱", player.content.decode().split('class="player-head"')[1])
        self.assertContains(player, "−1,800 chips")

    def test_reading_writes_nothing(self):
        from audit.models import AuditEvent
        from ledger.models import PlayerResult

        before = (AuditEvent.objects.count(), PlayerResult.objects.count())
        self.stats(sort="return", period="recent")
        self.player(self.ana)
        self.assertEqual((AuditEvent.objects.count(), PlayerResult.objects.count()), before)

    def test_your_summary(self):
        self.assertContains(self.stats(), "You have no closed session")
        self.client.force_login(self.viewer.user)
        self.assertContains(self.stats(), "You have no closed session")
        user = make_user("ana-login")
        type(self.ana).objects.filter(pk=self.ana.pk).update(user=user)
        self.client.force_login(user)
        page = self.stats()
        self.assertContains(page, "1st of 2")
        self.assertContains(page, "Your stats")
        self.assertContains(page, "Last result")

    def test_player_page_figures_match_a_hand_calculation(self):
        page = self.player(self.ana)
        tiles = {t.label: t.text for t in page.context["tiles"]}
        self.assertEqual(tiles["Average per session"], "+₱280")
        self.assertEqual(tiles["Return on buy-ins"], "+28%")
        self.assertEqual(tiles["Win rate"], "80%")
        self.assertEqual(tiles["Total bought in"], "₱5,000")
        self.assertEqual(tiles["Rebuys per session"], "0.0")
        self.assertEqual(tiles["Per hour"], "—")
        self.assertContains(page, "+₱1,400")
        self.assertContains(page, "1st of 2")
        self.assertContains(page, "5 sessions since Aug 2026")
        self.assertContains(page, "Won 2 in a row")
        self.assertContains(page, "Best night")
        self.assertContains(page, "Running profit")
        self.assertEqual(len(page.context["chart"].points), 5)
        self.assertEqual(len(page.context["sessions"]), 5)

    def test_no_chart_under_three_sessions_and_show_all(self):
        page = self.player(self.carlo)
        self.assertIsNone(page.context["chart"])
        self.assertContains(page, "The chart appears after three sessions.")
        self.assertContains(page, "Not ranked yet")
        for _ in range(7):
            self.club.session(D(2026, 10, 8), {"Ana": (1000, 1000), "Ben": (1000, 1000)})
        page = self.player(self.ana)
        self.assertEqual(len(page.context["sessions"]), 10)
        self.assertContains(page, "Show all 12")
        self.assertEqual(len(self.player(self.ana, all="1").context["sessions"]), 12)

    def test_a_removed_player_keeps_a_page_and_a_place(self):
        groups.remove_member(self.host, self.ben.pk)
        self.assertContains(self.stats(), "Left the group")
        self.assertContains(self.player(self.ben), "Left the group")

    def test_only_members_of_the_group(self):
        other_group, other_host = make_group("omar", "Other")
        stranger = groups.add_roster_player(other_host, "Stranger")
        self.assertEqual(self.player(stranger).status_code, 404)
        self.client.force_login(other_host.user)
        self.assertEqual(self.player(self.ana).status_code, 404)

    def test_query_counts_do_not_grow(self):
        def count(get):
            with CaptureQueriesContext(connection) as queries:
                get()
            return len(queries)

        board, page = count(self.stats), count(lambda: self.player(self.ana))
        for day in (D(2026, 10, 5), D(2026, 10, 6)):
            self.club.session(day, {name: (1000, 1000) for name in ("Ana", "Ben", "Carlo", "Dani", "Eli", "Fe")})
        self.assertEqual((count(self.stats), count(lambda: self.player(self.ana))), (board, page))

    @override_settings(STATS_PAGES=False)
    def test_switch_off(self):
        page = self.stats()
        self.assertContains(page, "Player stats")
        self.assertNotContains(page, "Not ranked yet")
        self.assertEqual(self.player(self.ana).status_code, 404)
