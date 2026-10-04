"""Group statistics read frozen results of closed sessions. They write nothing."""

import datetime
import uuid

from django.test import TestCase
from django.urls import reverse

from games import services as games
from games.tests.helpers import CHIP_STAKES, make_session, make_table
from groups import services as groups
from groups.tests.helpers import add_player, make_group, make_user
from ledger import services as ledger
from ledger.models import PlayerResult
from settlement import queries, services

from .test_night import TwoSets

SEP_30 = datetime.date(2026, 9, 30)
OCT_1 = datetime.date(2026, 10, 1)


class Club:
    """One group that plays several sessions. Figures are whole pesos, or chips in a chips session."""

    def __init__(self):
        self.group, self.host = make_group()
        self.table = make_table(self.host)
        self.members = {}

    def member(self, name):
        if name not in self.members:
            self.members[name] = groups.add_roster_player(self.host, name)
        return self.members[name]

    def session(self, date, figures, *, unit="php", close=True, cancel=False, **settings):
        """``figures`` is ``{name: (bought in, cashed out)}`` for a one-set session."""
        scale = 1 if unit == "chips" else 100
        if unit == "chips":
            settings = {**CHIP_STAKES, "unit": "chips", **settings}
        one = make_session(self.host, table=self.table, state="open", game_date=date, **settings)
        seats = games.add_participants(one.pk, self.host, [self.member(n).pk for n in figures], uuid.uuid4())
        games.transition(one.pk, self.host, "start", opening_buy_ins=False)
        if cancel:  # a set with money cannot be canceled, so cancel before any buy-in
            return games.transition(one.pk, self.host, "cancel", "Synthetic cancellation")
        for seat, (bought, _) in zip(seats, figures.values()):
            ledger.record_buy_in(one.pk, self.host, seat.pk, bought * scale, uuid.uuid4())
        games.transition(one.pk, self.host, "end")
        for seat, (_, cashed) in zip(seats, figures.values()):
            ledger.record_cash_out(one.pk, self.host, seat.pk, cashed * scale, uuid.uuid4())
        services.finalize(one.pk, self.host)
        if close:
            services.close_night(one.night_id, self.host)
        return one

    def stats(self, unit="php", month=None):
        return {s.member.display_name: (s.net, s.sessions, s.wins) for s in queries.group_stats(self.group, unit, month)}


class GroupStatsTests(TestCase):
    def test_sets_of_one_session_are_added_before_counting(self):
        two = TwoSets()  # A +600 then −400; B −300 then +400; C −300 then 0
        group = two.host.group
        self.assertEqual(queries.group_stats(group, "php"), [])  # the session is still open
        self.assertEqual(queries.stat_periods(group), {})
        services.close_night(two.night_id, two.host)
        stats = queries.group_stats(group, "php")
        self.assertEqual([(s.member.display_name, s.net, s.sessions, s.wins) for s in stats],
                         [("A", 20000, 1, 1), ("B", 10000, 1, 1), ("C", -30000, 1, 0)])
        self.assertEqual(sum(s.net for s in stats), 0)
        self.assertEqual(sum(s.net for s in stats), sum(PlayerResult.objects.filter(is_current=True).values_list("net", flat=True)))

    def test_month_uses_the_session_date_and_break_even_is_played_not_won(self):
        club = Club()
        club.session(SEP_30, {"A": (1000, 1500), "B": (1000, 500)})
        club.session(OCT_1, {"A": (1000, 1000), "B": (1000, 800), "C": (1000, 1200)})
        self.assertEqual(club.stats(), {"A": (50000, 2, 1), "B": (-70000, 2, 0), "C": (20000, 1, 1)})
        self.assertEqual(club.stats(month=SEP_30), {"A": (50000, 1, 1), "B": (-50000, 1, 0)})
        self.assertEqual(club.stats(month=datetime.date(2026, 10, 31)),
                         {"A": (0, 1, 0), "B": (-20000, 1, 0), "C": (20000, 1, 1)})
        self.assertEqual(queries.stat_periods(club.group), {"php": [OCT_1, datetime.date(2026, 9, 1)]})
        a = next(s for s in queries.group_stats(club.group, "php") if s.member.display_name == "A")
        self.assertEqual(a.win_percent, 50)
        self.assertEqual([s.member.display_name for s in queries.group_stats(club.group, "php")], ["A", "C", "B"])

    def test_profit_is_the_result_after_rake_not_the_settle_up_balance(self):
        club = Club()
        one = club.session(OCT_1, {"A": (1000, 1960), "B": (1000, 0)}, rake_mode="flat", rake_flat=2000)
        self.assertEqual(club.stats(), {"A": (96000, 1, 1), "B": (-100000, 1, 0)})
        balances = dict(services.settlement_balances(one.night))
        self.assertEqual(balances[club.member("A").pk], 98000)  # the balance adds the fee back; stats do not

    def test_units_are_separate_and_never_summed(self):
        club = Club()
        club.session(OCT_1, {"A": (1000, 1500), "B": (1000, 500)})
        club.session(OCT_1, {"A": (1000, 400), "B": (1000, 1600)}, unit="chips")
        self.assertEqual(club.stats("php"), {"A": (50000, 1, 1), "B": (-50000, 1, 0)})
        self.assertEqual(club.stats("chips"), {"A": (-600, 1, 0), "B": (600, 1, 1)})
        self.assertEqual(set(queries.stat_periods(club.group)), {"php", "chips"})

    def test_open_sessions_canceled_sets_and_old_snapshots_do_not_count(self):
        club = Club()
        club.session(OCT_1, {"A": (1000, 1500), "B": (1000, 500)}, close=False)
        club.session(OCT_1, {"A": (1000, 0)}, cancel=True)
        self.assertEqual(club.stats(), {})
        counted = club.session(OCT_1, {"A": (1000, 1200), "B": (1000, 800)})
        self.assertEqual(club.stats(), {"A": (20000, 1, 1), "B": (-20000, 1, 0)})
        PlayerResult.objects.filter(finalization__session=counted).update(is_current=False)
        self.assertEqual(club.stats(), {})

    def test_other_groups_and_removed_or_loginless_players(self):
        club, other = Club(), Club()
        club.session(OCT_1, {"A": (1000, 1500), "B": (1000, 500)})
        other.session(OCT_1, {"Z": (1000, 2000), "Y": (1000, 0)})
        self.assertEqual(set(club.stats()), {"A", "B"})
        groups.remove_member(club.host, club.member("B").pk)
        self.assertEqual(club.stats()["B"], (-50000, 1, 0))  # history keeps a player who left the group

    def test_the_number_of_queries_does_not_grow_with_players(self):
        club = Club()
        club.session(OCT_1, {name: (1000, 1000) for name in "ABCDEFGH"})
        with self.assertNumQueries(2):
            self.assertEqual(len(queries.group_stats(club.group, "php")), 8)


class GroupStatsPageTests(TestCase):
    def setUp(self):
        self.club = Club()
        self.url = reverse("group", args=[self.club.group.pk])
        self.client.force_login(self.club.host.user)

    def test_tab_appears_only_with_a_closed_session(self):
        self.club.session(OCT_1, {"A": (1000, 1500), "B": (1000, 500)}, close=False)
        self.assertNotContains(self.client.get(self.url), "view=stats")
        page = self.client.get(self.url, {"view": "stats"})
        self.assertContains(page, "No stats yet")
        self.club.session(OCT_1, {"A": (1000, 1500), "B": (1000, 500)})
        self.assertContains(self.client.get(self.url), f'{self.url}?view=stats"')
        self.assertContains(self.client.get(self.url, {"view": "settings"}), f'{self.url}?view=stats"')

    def test_page_shows_figures_definitions_and_period_choice(self):
        self.club.session(SEP_30, {"A": (1000, 1500), "B": (1000, 500)})
        self.club.session(OCT_1, {"A": (1000, 1000), "B": (1000, 1000)})
        page = self.client.get(self.url, {"view": "stats"})
        self.assertContains(page, "+₱500")
        self.assertContains(page, "−₱500")
        self.assertContains(page, "2 sessions · won 1 · 50% win rate")
        self.assertContains(page, "not a rate of hands won")
        self.assertContains(page, "after rake")
        self.assertContains(page, "month=2026-09")
        self.assertNotContains(page, 'aria-label="Unit"')  # one unit: no unit choice
        month = self.client.get(self.url, {"view": "stats", "month": "2026-10"})
        self.assertContains(month, "Sessions dated October 2026")
        self.assertContains(month, "1 session · won 0 · 0% win rate")
        self.assertNotContains(month, "+₱500")
        # An unknown month or unit falls back instead of failing.
        self.assertContains(self.client.get(self.url, {"view": "stats", "month": "junk", "unit": "gold"}), "Every closed session")

    def test_chips_choice_never_shows_pesos(self):
        self.club.session(OCT_1, {"A": (1000, 1500), "B": (1000, 500)})
        self.club.session(OCT_1, {"A": (1000, 400), "B": (1000, 1600)}, unit="chips")
        page = self.client.get(self.url, {"view": "stats", "unit": "chips"})
        self.assertContains(page, 'aria-label="Unit"')
        self.assertContains(page, "+600 chips")
        body = page.content.decode().split('<ol class="stat-list">')[1].split("</ol>")[0]
        self.assertNotIn("₱", body)

    def test_player_can_read_and_outsider_cannot(self):
        self.club.session(OCT_1, {"A": (1000, 1500), "B": (1000, 500)})
        self.client.force_login(add_player(self.club.group, "viewer").user)
        self.assertContains(self.client.get(self.url, {"view": "stats"}), "Player stats")
        self.client.force_login(make_user("outsider"))
        self.assertEqual(self.client.get(self.url, {"view": "stats"}).status_code, 404)

    def test_reading_stats_writes_nothing(self):
        from audit.models import AuditEvent
        self.club.session(OCT_1, {"A": (1000, 1500), "B": (1000, 500)})
        before = (AuditEvent.objects.count(), PlayerResult.objects.count())
        self.client.get(self.url, {"view": "stats"})
        self.assertEqual((AuditEvent.objects.count(), PlayerResult.objects.count()), before)
