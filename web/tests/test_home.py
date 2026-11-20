"""The Your groups page reports each group's state from batched read-only queries."""

import datetime
import uuid

from django.test import TestCase
from django.urls import reverse
from django.utils.html import strip_tags

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
        self.assertEqual((card.kind, card.action_label), ("quiet", "New session"))
        self.assertTrue(card.action_url.endswith("/sessions/new/"))
        make_table(self.host)
        card = card_for(self.host.user, self.group)
        self.assertEqual((card.action_label, card.action_primary), ("New session", True))
        self.assertEqual(card_for(self.player.user, self.group).action_label, "")

    def test_each_set_state_chooses_its_action(self):
        one = make_session(self.host, state="setup")
        host = card_for(self.host.user, self.group)
        self.assertEqual((host.kind, host.action_label, host.action_primary), ("open", "Go to set 1", True))
        # A draft is for hosts only: the player's card stays quiet.
        self.assertEqual(card_for(self.player.user, self.group).kind, "quiet")
        games.transition(one.pk, self.host, "open")
        player = card_for(self.player.user, self.group)
        self.assertEqual((player.kind, player.action_label, player.action_primary), ("open", "Go to set 1", True))
        seat = games.add_participant(one.pk, self.host, self.player.pk)
        games.transition(one.pk, self.host, "start", opening_buy_ins=False)
        for user in (self.host.user, self.player.user):
            card = card_for(user, self.group)
            self.assertEqual((card.kind, card.action_label, card.at_table), ("play", "Go to the table", 1))
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
        # 10, and one for the viewer's unseen "added you" notices (notify.services.unseen).
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
        self.assertContains(page, f'href="{reverse("session", args=[live.pk])}">Go to the table</a>')
        self.assertContains(page, "data-running")
        self.assertNotContains(page, "in play ·")  # no money figure on this page
        self.assertNotContains(page, "New session")

    def test_each_card_has_one_settings_button_and_its_name_opens_the_group(self):
        group = self.club.group
        for user, gears in ((self.club.host.user, 1), (self.user_a, 0)):  # a player reaches Settings by the group's tab
            self.client.force_login(user)
            html = self.client.get(self.url).content.decode()
            settings = reverse("group", args=[group.pk]) + "?view=settings"
            self.assertEqual(html.count(f'href="{settings}"'), gears)
            self.assertEqual(html.count(f'<a class="btn btn-round btn-quiet group-gear" href="{settings}" aria-label="Group settings for {group.name}">'), gears)
            self.assertRegex(html, rf'<h2 id="group-{group.pk}"><a href="{reverse("group", args=[group.pk])}">')
            self.assertNotIn("home-links", html)

    def test_players_beyond_the_chips_are_a_number_and_the_count_is_still_read_out(self):
        for n in range(8):
            groups.add_roster_player(self.club.host, f"Extra {n}")
        self.client.force_login(self.club.host.user)
        html = self.client.get(self.url).content.decode()
        total = len(card_for(self.club.host.user, self.club.group).members)
        self.assertEqual(html.count('class="chip k'), 6)
        self.assertIn(f'<span class="chip-more" aria-hidden="true">+{total - 1 - 6}</span>', html)  # the viewer has no chip
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

    def _record_rows(self, html):
        """The rows of Your record, as HTML, in page order (2026-11-19: rows, not tiles)."""
        part = html.split('<ul class="home-record"')[1]
        part = part[:part.index("</ul>")]
        return [row[:row.index("</li>")] for row in part.split("<li")[1:]]

    def test_my_record_is_one_net_row_with_sessions_and_win_rate_as_its_note(self):
        self.club.session(SEP_30, {"A": (1000, 1500), "B": (1000, 500)})
        self.club.session(OCT_1, {"A": (1000, 800), "B": (1000, 1200)})
        self.club.session(OCT_1, {"A": (1000, 1100), "B": (1000, 900)})
        self.client.force_login(self.user_a)
        html = self.client.get(self.url).content.decode()
        self.assertEqual(html.count("Your record</h3>"), 1)
        net, last = self._record_rows(html)
        self.assertIn("<strong>Net</strong>", net)
        # Two wins in three: 66%, rounded down as Stats rounds it.
        self.assertIn("3 sessions · 66% win rate", strip_tags(net))
        self.assertIn("+₱400", net)
        self.assertIn('class="amount plus"', net)
        self.assertNotIn("<a ", net)  # the record is read, not pressed
        record = card_for(self.user_a, self.club.group).records[0][1]
        self.assertEqual((record.sessions, record.win_percent, record.net), (3, 66, 40000))
        self.assertIn("<strong>Last session</strong>", last)
        self.assertIn("+₱100", last)

    def test_each_unit_has_its_own_row_and_a_loss_keeps_its_sign(self):
        self.club.session(SEP_30, {"A": (1000, 500), "B": (1000, 1500)})
        self.club.session(OCT_1, {"A": (1000, 1600), "B": (1000, 400)}, unit="chips")
        self.client.force_login(self.user_a)
        html = self.client.get(self.url).content.decode()
        self.assertEqual(html.count("Your record</h3>"), 1)  # one label over both units
        self.assertNotIn('<span class="count-pill">Chips</span>', html)
        pesos, chips, last = self._record_rows(html)
        self.assertIn("<strong>Net in pesos</strong>", pesos)
        self.assertIn("1 session · 0% win rate", strip_tags(pesos))
        self.assertIn("−₱500", pesos)
        self.assertIn('class="amount minus"', pesos)
        self.assertIn("<strong>Net in chips</strong>", chips)
        self.assertIn("1 session · 100% win rate", strip_tags(chips))
        self.assertIn("+600 chips", chips)
        self.assertNotIn("₱", chips)
        self.assertIn("+600 chips", last)

    def test_last_session_is_a_row_that_opens_the_session(self):
        one = self.club.session(OCT_1, {"A": (1000, 500), "B": (1000, 1500)})
        self.client.force_login(self.user_a)
        *_, last = self._record_rows(self.client.get(self.url).content.decode())
        self.assertIn('class="row-card press-card home-last"', last)
        self.assertIn(f'<a class="card-link" href="{reverse("night", args=[one.night_id])}"', last)
        self.assertIn("Oct 1", last)

    def test_an_even_record_has_no_sign_and_no_icon(self):
        self.club.session(OCT_1, {"A": (1000, 1000), "B": (1000, 1000)})
        self.client.force_login(self.user_a)
        net, last = self._record_rows(self.client.get(self.url).content.decode())
        for row in (net, last):
            self.assertIn("₱0", row)
            self.assertNotIn("icon-minus", row)
            self.assertNotIn("−₱0", row)

    def test_no_session_played_means_no_net_row_and_a_quiet_did_not_play(self):
        self.club.session(OCT_1, {"B": (1000, 1000)})
        self.client.force_login(self.club.host.user)
        html = self.client.get(self.url).content.decode()
        [last] = self._record_rows(html)
        self.assertNotIn("Net", last)
        self.assertIn('<span class="home-absent">Did not play</span>', last)
        self.assertNotContains(self.client.get(self.url), "Your record")

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
        self.assertNotContains(page, '<details class="home-create"')
        self.assertContains(page, '<details hidden class="home-create home-link"', count=1)
        self.client.force_login(self.club.host.user)
        page = self.client.get(self.url)
        self.assertContains(page, '<details class="home-create" >')
        refused = self.client.post(reverse("group_create"), {"name": "G" * 61}, follow=True)
        self.assertContains(refused, '<details class="home-create" open>')
        self.assertContains(refused, "G" * 61)


class HomeTokenTests(TestCase):
    """The card's chips show who played last, not the first names by the alphabet."""

    def setUp(self):
        self.club = Club()
        for name in ("Aaron", "Abby"):  # in the group, never played
            self.club.member(name)

    def names(self, user):
        card = card_for(user, self.club.group)
        return [m.display_name for m in card.tokens], card.more_members

    def test_latest_session_first_then_earlier_then_the_rest_by_name(self):
        self.club.session(SEP_30, {"D": (1000, 1000), "C": (1000, 1000)})
        self.club.session(OCT_1, {"F": (1000, 1000), "E": (1000, 1000)})
        tokens, more = self.names(self.club.host.user)
        self.assertEqual(tokens, ["E", "F", "C", "D", "Aaron", "Abby"])
        self.assertEqual(more, 0)

    def test_the_viewer_is_not_a_token(self):
        self.club.session(OCT_1, {"E": (1000, 1000), "F": (1000, 1000)})
        viewer = make_user("eve")
        Member.objects.filter(pk=self.club.member("E").pk).update(user=viewer)
        tokens, _ = self.names(viewer)
        self.assertNotIn("E", tokens)
        self.assertEqual(tokens[0], "F")

    def test_a_canceled_set_is_not_play(self):
        self.club.session(SEP_30, {"C": (1000, 1000), "D": (1000, 1000)})
        self.club.session(OCT_1, {"Abby": (0, 0)}, cancel=True)
        tokens, _ = self.names(self.club.host.user)
        self.assertEqual(tokens[:2], ["C", "D"])

    def test_a_draft_set_or_a_future_session_is_not_play(self):
        self.club.session(SEP_30, {"C": (1000, 1000), "D": (1000, 1000)})
        draft = make_session(self.club.host, table=self.club.table, state="setup", game_date=OCT_1)
        games.add_participants(draft.pk, self.club.host, [self.club.member("Abby").pk], uuid.uuid4())
        later = make_session(self.club.host, table=make_table(self.club.host, name="Later"), state="open",
                             game_date=datetime.date.today() + datetime.timedelta(days=7))
        games.add_participants(later.pk, self.club.host, [self.club.member("Aaron").pk], uuid.uuid4())
        tokens, _ = self.names(self.club.host.user)
        self.assertEqual(tokens[:2], ["C", "D"])

    def test_more_counts_the_others_not_shown(self):
        for name in "BCDEFGH":
            self.club.member(name)
        tokens, more = self.names(self.club.host.user)
        self.assertEqual(len(tokens), 6)
        self.assertEqual(more, 3)  # 9 others than the host, 6 shown

    def test_a_group_with_no_play_keeps_the_order_by_name(self):
        tokens, _ = self.names(self.club.host.user)
        self.assertEqual(tokens, ["Aaron", "Abby"])


class HomeCardForPlayersTests(TestCase):
    def setUp(self):
        self.club = Club()
        self.player = make_user("pia")
        Member.objects.filter(pk=self.club.member("P").pk).update(user=self.player)

    def test_the_gear_is_for_hosts_only(self):
        self.client.force_login(self.club.host.user)
        self.assertContains(self.client.get(reverse("home")), "group-gear")
        self.client.force_login(self.player)
        self.assertNotContains(self.client.get(reverse("home")), "group-gear")

    def test_more_unpaid_transfers_link_to_the_not_settled_list(self):
        from django.test import override_settings
        for day in range(1, 6):
            self.club.session(datetime.date(2026, 9, day), {"P": (1000, 0), "Q": (1000, 2000)})
        self.client.force_login(self.player)
        with override_settings(DEBTS_VIEW=False):
            page = self.client.get(reverse("home"))
        url = reverse("group", args=[self.club.group.pk]) + "?past=unsettled#past-sessions"
        self.assertContains(page, f'href="{url}"')
        self.assertContains(page, "2 more unpaid transfers")
