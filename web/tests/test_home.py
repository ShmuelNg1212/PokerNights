"""The Your groups page reports each group's state from batched read-only queries."""

import datetime
import uuid

from django.test import TestCase
from django.urls import reverse

from games import services as games
from games.models import GameNight
from games.tests.helpers import make_session, make_table
from groups import services as groups
from groups.models import Member
from groups.tests.helpers import add_player, make_group, make_user
from ledger import services as ledger
from settlement import queries, services
from settlement.tests.test_stats import OCT_1, SEP_30, Club
from web.home import home_cards


def card_for(user, group):
    return next(card for card in home_cards(user) if card.group.pk == group.pk)


class HomeStatusTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.player = add_player(self.group, "viewer")

    def test_quiet_group_gives_the_host_one_next_action_and_a_player_none(self):
        card = card_for(self.host.user, self.group)
        self.assertEqual((card.kind, card.action_label), ("quiet", "Add a table"))
        self.assertTrue(card.action_url.endswith("?view=settings#tables"))
        make_table(self.host)
        card = card_for(self.host.user, self.group)
        self.assertEqual((card.action_label, card.action_primary), ("New session", True))
        self.assertEqual(card_for(self.player.user, self.group).action_label, "")

    def test_each_set_state_chooses_its_action(self):
        one = make_session(self.host, state="setup")
        host = card_for(self.host.user, self.group)
        self.assertEqual((host.kind, host.action_label, host.action_primary), ("open", "Open set 1", True))
        # A draft is for hosts only: the player's card stays quiet.
        self.assertEqual(card_for(self.player.user, self.group).kind, "quiet")
        games.transition(one.pk, self.host, "open")
        player = card_for(self.player.user, self.group)
        self.assertEqual((player.kind, player.action_label, player.action_primary), ("open", "Open set 1", True))
        seat = games.add_participant(one.pk, self.host, self.player.pk)
        games.transition(one.pk, self.host, "start", opening_buy_ins=False)
        for user in (self.host.user, self.player.user):
            card = card_for(user, self.group)
            self.assertEqual((card.kind, card.action_label, card.at_table), ("play", "Open the table", 1))
            self.assertEqual(card.action_url, reverse("session", args=[one.pk]))
            self.assertIsNotNone(card.seconds)
        ledger.record_buy_in(one.pk, self.host, seat.pk, 100000, uuid.uuid4())
        games.transition(one.pk, self.host, "end")
        self.assertEqual(card_for(self.host.user, self.group).action_primary, True)
        self.assertEqual(card_for(self.player.user, self.group).action_primary, False)
        ledger.record_cash_out(one.pk, self.host, seat.pk, 100000, uuid.uuid4())
        services.finalize(one.pk, self.host)
        card = card_for(self.host.user, self.group)
        self.assertEqual((card.kind, card.action_label), ("open", "Go to the session"))
        self.assertEqual(card.action_url, reverse("night", args=[one.night_id]))
        services.close_night(one.night_id, self.host)
        card = card_for(self.host.user, self.group)
        self.assertEqual((card.kind, card.action_label), ("quiet", "New session"))
        self.assertEqual(card.last_night.pk, one.night_id)

    def test_a_set_in_play_wins_over_other_open_sessions_and_sorts_first(self):
        table = make_table(self.host)
        make_session(self.host, table=table, state="open", game_date=datetime.date(2026, 10, 20))
        live = make_session(self.host, table=table, state="running", game_date=datetime.date(2026, 10, 1))
        card = card_for(self.host.user, self.group)
        self.assertEqual((card.kind, card.set.pk, card.more_open), ("play", live.pk, 1))
        other = groups.create_group(self.host.user, "Aardvark Club")
        self.assertEqual([c.group.name for c in home_cards(self.host.user)], ["Friday Game", "Aardvark Club"])
        self.assertEqual(card_for(self.host.user, other.group).members, [other])


class HomeFiguresTests(TestCase):
    def setUp(self):
        self.club = Club()
        self.user_a = make_user("anna")
        self.a = self.club.member("A")
        Member.objects.filter(pk=self.a.pk).update(user=self.user_a)

    def test_record_and_last_result_match_the_stats_for_the_same_data(self):
        self.club.session(SEP_30, {"A": (1000, 1500), "B": (1000, 500)})
        last = self.club.session(OCT_1, {"A": (1000, 800), "B": (1000, 1200)})
        self.club.session(OCT_1, {"A": (1000, 400), "B": (1000, 1600)}, unit="chips", close=False)
        card = card_for(self.user_a, self.club.group)
        self.assertEqual([(unit, s.net, s.sessions) for unit, s in card.records], [("php", 30000, 2)])
        stats = {s.member.pk: s.net for s in queries.group_stats(self.club.group, "php")}
        self.assertEqual(card.records[0][1].net, stats[self.a.pk])
        self.assertEqual((card.last_night.pk, card.last_net), (last.night_id, -20000))
        # The host did not play: no record and no result, but the last session is still named.
        host = card_for(self.club.host.user, self.club.group)
        self.assertEqual((host.records, host.last_net, host.last_night.pk), ([], None, last.night_id))

    def test_units_stay_apart(self):
        self.club.session(OCT_1, {"A": (1000, 1500), "B": (1000, 500)})
        self.club.session(OCT_1, {"A": (1000, 400), "B": (1000, 1600)}, unit="chips")
        card = card_for(self.user_a, self.club.group)
        self.assertEqual([(unit, s.net) for unit, s in card.records], [("php", 50000), ("chips", -600)])

    def test_dues_follow_the_transfer_plan_and_paid_marks(self):
        one = self.club.session(OCT_1, {"A": (1000, 500), "B": (1000, 1500)})
        night = GameNight.objects.get(pk=one.night_id)
        transfer = queries.night_outcome(night).transfers[0]
        card = card_for(self.user_a, self.club.group)
        self.assertEqual([(d.owes, d.other.display_name, d.amount, d.unit) for d in card.dues], [(True, "B", 50000, "php")])
        self.assertEqual(card_for(self.club.host.user, self.club.group).dues, [])  # not the host's debt
        services.mark_paid(night.pk, self.club.host, transfer.pk, uuid.uuid4())
        self.assertEqual(card_for(self.user_a, self.club.group).dues, [])
        services.mark_unpaid(night.pk, self.club.host, transfer.pk)
        self.assertEqual(len(card_for(self.user_a, self.club.group).dues), 1)
        user_b = make_user("bea")
        Member.objects.filter(pk=self.club.member("B").pk).update(user=user_b)
        due = card_for(user_b, self.club.group).dues[0]
        self.assertEqual((due.owes, due.other.display_name, due.amount), (False, "A", 50000))

    def test_other_groups_and_former_members_are_not_shown(self):
        other = Club()
        other.session(OCT_1, {"Z": (1000, 2000), "Y": (1000, 0)})
        self.club.session(OCT_1, {"A": (1000, 1500), "B": (1000, 500)})
        cards = home_cards(self.user_a)
        self.assertEqual([c.group.pk for c in cards], [self.club.group.pk])
        self.assertEqual([(d.owes, d.other.display_name) for d in cards[0].dues], [(False, "B")])  # nothing from the other club
        groups.remove_member(self.club.host, self.a.pk)
        self.assertEqual(home_cards(self.user_a), [])

    def test_query_count_does_not_grow_with_groups_or_players(self):
        def build(club):
            names = {name: (1000, 1000) for name in "ABCDEFGH"}
            club.session(SEP_30, names)
            live = make_session(club.host, table=club.table, state="open")
            games.add_participants(live.pk, club.host, [club.member(n).pk for n in names], uuid.uuid4())
            games.transition(live.pk, club.host, "start", opening_buy_ins=False)
        user = self.club.host.user
        build(self.club)
        with self.assertNumQueries(11):
            self.assertEqual(len(home_cards(user)), 1)
        for name in ("Second", "Third", "Fourth"):
            club = Club.__new__(Club)
            club.host = groups.create_group(user, name)
            club.group, club.table, club.members = club.host.group, make_table(club.host), {}
            build(club)
        with self.assertNumQueries(11):
            self.assertEqual(len(home_cards(user)), 4)


class HomePageTests(TestCase):
    def setUp(self):
        self.club = Club()
        self.user_a = make_user("anna")
        Member.objects.filter(pk=self.club.member("A").pk).update(user=self.user_a)
        self.url = reverse("home")

    def test_set_in_play_is_one_tap_away_and_is_the_only_felt(self):
        self.client.force_login(self.club.host.user)
        quiet = self.client.get(self.url)
        self.assertNotContains(quiet, "felt")
        self.assertContains(quiet, "No session in progress")
        self.assertContains(quiet, "New session", count=1)
        live = make_session(self.club.host, table=self.club.table, state="running")
        page = self.client.get(self.url)
        self.assertContains(page, 'class="home-band felt"', count=1)
        self.assertContains(page, f'href="{reverse("session", args=[live.pk])}">Open the table</a>')
        self.assertContains(page, "data-running")
        self.assertNotContains(page, "in play ·")  # no money figure on this page
        self.assertNotContains(page, "New session")

    def test_each_card_has_one_settings_button_and_its_name_opens_the_group(self):
        group = self.club.group
        for user in (self.club.host.user, self.user_a):
            self.client.force_login(user)
            html = self.client.get(self.url).content.decode()
            settings = reverse("group", args=[group.pk]) + "?view=settings"
            self.assertEqual(html.count(f'href="{settings}"'), 1)
            self.assertIn(f'<a class="btn btn-round btn-quiet group-gear" href="{settings}" aria-label="Group settings for {group.name}">', html)
            self.assertRegex(html, rf'<h2 id="group-{group.pk}"><a href="{reverse("group", args=[group.pk])}">')
            self.assertNotIn("home-links", html)

    def test_players_beyond_the_chips_are_a_number_and_the_count_is_still_read_out(self):
        for n in range(8):
            groups.add_roster_player(self.club.host, f"Extra {n}")
        self.client.force_login(self.club.host.user)
        html = self.client.get(self.url).content.decode()
        total = len(card_for(self.club.host.user, self.club.group).members)
        self.assertEqual(html.count('class="chip k'), 6)
        self.assertIn(f'<span class="chip-more" aria-hidden="true">+{total - 6}</span>', html)
        self.assertIn(f'<span class="visually-hidden">{total} players</span>', html)

    def test_my_figures_are_mine_only(self):
        one = self.club.session(OCT_1, {"A": (1000, 500), "B": (1000, 1500)})
        self.client.force_login(self.user_a)
        mine = self.client.get(self.url)
        self.assertContains(mine, "You owe <strong>B</strong>")
        self.assertContains(mine, "₱500")
        self.assertContains(mine, "Your record")
        self.assertContains(mine, "−₱500")
        self.assertContains(mine, reverse("night", args=[one.night_id]))
        self.assertNotContains(mine, "?view=stats")  # the card has one settings button, no Sessions or Stats links
        self.assertNotContains(mine, "New session")  # a player gets no host action
        self.client.force_login(self.club.host.user)
        host = self.client.get(self.url)
        self.assertNotContains(host, "To settle")
        self.assertNotContains(host, "Your record")
        self.assertContains(host, "Did not play")
        self.assertNotContains(host, "You did not play")

    def test_player_never_sees_a_draft(self):
        make_session(self.club.host, table=self.club.table, state="setup")
        self.client.force_login(self.user_a)
        page = self.client.get(self.url)
        self.assertContains(page, "No session in progress")
        self.assertNotContains(page, "Draft")
        self.client.force_login(self.club.host.user)
        self.assertContains(self.client.get(self.url), "Set 1 · Draft")

    def test_first_group_and_create_another(self):
        self.client.force_login(make_user("newcomer"))
        page = self.client.get(self.url)
        self.assertContains(page, "Start your first group")
        self.assertNotContains(page, "<details")
        self.client.force_login(self.club.host.user)
        page = self.client.get(self.url)
        self.assertContains(page, '<details class="home-create" >')
        refused = self.client.post(reverse("group_create"), {"name": "G" * 61}, follow=True)
        self.assertContains(refused, '<details class="home-create" open>')
        self.assertContains(refused, "G" * 61)
