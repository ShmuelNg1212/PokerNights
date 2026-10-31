"""The Players tab: the list, your own name, details, removing and bringing back, several names."""

from django.test import TestCase, override_settings
from django.urls import reverse

from games.tests.test_add_players import Roster
from groups import services as groups
from groups.models import Member
from groups.tests.helpers import add_player, make_group
from settlement.tests.test_stats import OCT_1, Club


def players_url(group):
    return reverse("group", args=[group.pk]) + "?view=players"


class RemovePageTests(TestCase):
    def setUp(self):
        self.club = Club()
        self.club.session(OCT_1, {"Ana": (1000, 1500), "Ben": (1000, 500)})
        self.ben = self.club.member("Ben")
        self.url = reverse("member_remove", args=[self.club.group.pk, self.ben.pk])
        self.client.force_login(self.club.host.user)

    def test_the_page_asks_and_lists_unpaid_transfers_without_removing(self):
        response = self.client.get(self.url)
        self.assertContains(response, "Remove Ben from the group?")
        self.assertContains(response, "results stay in past sessions and in Stats")
        self.assertContains(response, "Still to pay")
        self.assertContains(response, "₱500")
        self.assertContains(response, "Removing Ben does not settle them.")
        self.assertContains(response, "Keep Ben")
        self.assertNotContains(response, "can no longer open this group")  # Ben has no login
        self.assertEqual(Member.objects.get(pk=self.ben.pk).status, "active")

    def test_post_removes_and_says_where_to_bring_them_back(self):
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, players_url(self.club.group) + "#players")
        self.assertContains(response, "Ben was removed. Bring them back from Removed players.")
        self.assertEqual(Member.objects.get(pk=self.ben.pk).status, "removed")

    def test_a_player_with_a_login_is_told_about_access(self):
        dani = add_player(self.club.group, "dani")
        response = self.client.get(reverse("member_remove", args=[self.club.group.pk, dani.pk]))
        self.assertContains(response, "can no longer open this group")
        self.assertNotContains(response, "Still to pay")

    def test_a_seated_player_and_the_only_host_get_the_reason_and_no_button(self):
        roster = Roster()
        roster.add("Carlo")
        self.client.force_login(roster.host.user)
        url = reverse("member_remove", args=[roster.group.pk, roster.members["Carlo"].pk])
        response = self.client.get(url)
        self.assertContains(response, "Carlo is at the table in Friday table set 1.")
        self.assertContains(response, reverse("session", args=[roster.session.pk]))
        self.assertNotContains(response, "btn-danger")
        self.client.post(url)
        self.assertEqual(Member.objects.get(pk=roster.members["Carlo"].pk).status, "active")
        response = self.client.get(reverse("member_remove", args=[roster.group.pk, roster.host.pk]))
        self.assertContains(response, "A group needs at least one host.")
        self.assertNotContains(response, "btn-danger")

    def test_only_a_host_of_this_group(self):
        ana = add_player(self.club.group, "ana2")
        self.client.force_login(ana.user)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url).status_code, 403)
        _, other = make_group("omar", "Other")
        self.client.force_login(other.user)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertEqual(self.client.post(self.url).status_code, 404)
        self.client.force_login(self.club.host.user)
        self.assertEqual(self.client.get(reverse("member_remove", args=[self.club.group.pk, other.pk])).status_code, 404)


class PlayersSectionTests(TestCase):
    def setUp(self):
        self.club = Club()
        self.group, self.host = self.club.group, self.club.host
        self.club.session(OCT_1, {"Ana": (1000, 1500), "Ben": (1000, 500)})
        self.dani = add_player(self.group, "dani")
        self.client.force_login(self.host.user)

    def page(self):
        return self.client.get(players_url(self.group))

    def player_page(self, member):
        return self.client.get(reverse("player", args=[self.group.pk, member.pk]), {"from": "players"})

    def test_rows_say_how_often_a_player_comes(self):
        response = self.page()
        self.assertContains(response, "1 session · last played Oct 1", count=2)
        self.assertContains(response, "No sessions yet")
        self.client.force_login(self.dani.user)
        self.assertContains(self.page(), "1 session · last played Oct 1", count=2)  # every member sees it

    def test_names_are_in_order_whatever_their_capitals(self):
        groups.add_roster_players(self.host, ["zed", "Carlo"])
        names = [m.display_name for m in self.page().context["members"]]
        self.assertEqual(names, sorted(names, key=str.lower))
        self.assertLess(names.index("Carlo"), names.index("dani"))

    def test_a_row_leads_to_the_player_and_holds_no_management(self):
        ben = self.club.member("Ben")
        response = self.page()
        self.assertContains(response, f'href="{reverse("player", args=[self.group.pk, ben.pk])}?from=players"')
        self.assertNotContains(response, reverse("member_remove", args=[self.group.pk, ben.pk]))
        self.assertNotContains(response, "Manage Ben")
        self.assertNotContains(response, "Change your name")

    def test_the_way_back_follows_the_way_in(self):
        ben = self.club.member("Ben")
        page = self.player_page(ben)
        self.assertEqual(page.context["back_url"], f"{players_url(self.group)}#member-{ben.pk}")
        self.assertContains(page, '<span class="back-words">Players</span>')
        page = self.client.get(reverse("player", args=[self.group.pk, ben.pk]))
        self.assertIn("view=stats", page.context["back_url"])
        self.assertContains(page, '<span class="back-words">Stats</span>')

    def test_a_host_manages_another_player_on_their_page(self):
        ben = self.club.member("Ben")
        page = self.player_page(ben)
        self.assertContains(page, "Manage Ben")
        for name in ("member_rename", "member_remove"):
            self.assertContains(page, reverse(name, args=[self.group.pk, ben.pk]))

    def test_a_player_sees_no_management_on_anyone_elses_page(self):
        ben = self.club.member("Ben")
        groups.edit_member(self.host, ben.pk, "Ben", "0917 555 0101")
        self.client.force_login(self.dani.user)
        for other in (ben, self.host):
            page = self.player_page(other)
            self.assertEqual(page.status_code, 200)
            self.assertNotContains(page, f'action="/g/{self.group.pk}/')
            self.assertNotContains(page, "player-manage")
            self.assertNotContains(page, "0917 555 0101")
            self.assertNotContains(page, reverse("member_remove", args=[self.group.pk, other.pk]))

    def test_a_host_cannot_manage_themselves_or_a_removed_player(self):
        self.assertNotContains(self.player_page(self.host), "Manage ")
        self.assertNotContains(self.player_page(self.host), reverse("member_remove", args=[self.group.pk, self.host.pk]))
        ben = self.club.member("Ben")
        groups.remove_member(self.host, ben.pk)
        page = self.player_page(ben)
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, "player-manage")

    def test_a_link_made_for_one_player_waits_on_another_players_page(self):
        maria = add_player(self.group, "maria")
        self.client.post(reverse("member_reset_link", args=[self.group.pk, maria.pk]))
        self.assertNotContains(self.player_page(self.dani), "/accounts/reset/")
        self.assertContains(self.player_page(maria), "/accounts/reset/")
        self.assertNotContains(self.player_page(maria), "/accounts/reset/")  # shown once

    def test_a_refused_name_stays_on_the_players_page_with_manage_open(self):
        ben = self.club.member("Ben")
        response = self.client.post(reverse("member_rename", args=[self.group.pk, ben.pk]), {"name": "ana", "contact": "note"}, follow=True)
        self.assertEqual(response.redirect_chain[-1][0], f'{reverse("player", args=[self.group.pk, ben.pk])}?from=players&open=manage#manage')
        self.assertContains(response, '<details class="player-manage" open>')
        self.assertContains(response, 'value="ana"')
        self.assertContains(response, "note")

    def test_a_write_keeps_the_unit_the_period_and_the_way_in(self):
        ben = self.club.member("Ben")
        url = reverse("member_rename", args=[self.group.pk, ben.pk])
        page = self.client.get(reverse("player", args=[self.group.pk, ben.pk]), {"unit": "php", "period": "year"})
        self.assertContains(page, 'name="keep" value="period=year&amp;unit=php"')
        response = self.client.post(url, {"name": "Ben", "contact": "", "keep": "period=year&unit=php&evil=https://x.example"})
        self.assertEqual(response.url, f'{reverse("player", args=[self.group.pk, ben.pk])}?period=year&unit=php&open=manage#manage')
        self.assertIn("view=stats", self.client.get(response.url).context["back_url"])

    def test_a_refused_write_about_nobody_in_the_group_lands_on_the_tab_with_its_refusal(self):
        _, other = make_group("omar", "Other")
        response = self.client.post(reverse("member_reset_link", args=[self.group.pk, other.pk]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[-1][0], f"{players_url(self.group)}#players")

    def test_a_link_that_has_run_out_is_not_shown_as_new(self):
        maria = add_player(self.group, "maria")
        self.client.post(reverse("member_reset_link", args=[self.group.pk, maria.pk]))
        session = self.client.session
        session["new_reset_link"]["expires_at"] = "2020-01-01T00:00:00+00:00"
        session.save()
        self.assertNotContains(self.player_page(maria), "/accounts/reset/")
        self.assertNotIn("new_reset_link", self.client.session)

    def test_a_link_made_before_links_named_their_player_still_shows(self):
        maria = add_player(self.group, "maria")
        self.client.post(reverse("member_reset_link", args=[self.group.pk, maria.pk]))
        session = self.client.session
        del session["new_reset_link"]["member"]
        session.save()
        self.assertContains(self.player_page(maria), "/accounts/reset/")

    def test_a_new_link_is_inside_the_place_a_write_lands(self):
        maria = add_player(self.group, "maria")
        page = self.client.post(reverse("member_reset_link", args=[self.group.pk, maria.pk]), follow=True).content.decode()
        self.assertLess(page.index('id="manage"'), page.index("/accounts/reset/"))

    def test_a_long_list_gets_a_search(self):
        self.assertNotContains(self.page(), "data-roster-search")
        groups.add_roster_players(self.host, [f"P{n}" for n in range(11)])
        self.assertContains(self.page(), "data-roster-search")

    def test_your_own_name(self):
        response = self.player_page(self.host)
        self.assertContains(response, "Change your name", count=1)
        self.assertContains(response, f"You still log in as <strong>{self.host.user.username}</strong>", html=False)
        url = reverse("member_rename_self", args=[self.group.pk])
        response = self.client.post(url, {"name": "Hana R"}, follow=True)
        self.assertContains(response, "Your name is now Hana R.")
        self.client.force_login(self.dani.user)
        self.assertContains(self.player_page(self.dani), "Change your name", count=1)
        response = self.client.post(url, {"name": "hana r"}, follow=True)
        self.assertContains(response, "A player named hana r is already in this group.")
        self.assertContains(response, 'value="hana r"')  # the typing is kept, in an open disclosure
        self.assertEqual(Member.objects.get(pk=self.dani.pk).display_name, "dani")

    def test_a_host_saves_name_and_contact_and_a_player_never_sees_the_note(self):
        ben = self.club.member("Ben")
        url = reverse("member_rename", args=[self.group.pk, ben.pk])
        response = self.client.post(url, {"name": "Benjie", "contact": "0917 555 0101"}, follow=True)
        self.assertContains(response, "Saved.")
        self.assertContains(response, "0917 555 0101")
        self.assertContains(response, "Contact (optional)")
        self.client.force_login(self.dani.user)
        for response in (self.page(), self.player_page(ben)):
            self.assertContains(response, "Benjie")
            self.assertNotContains(response, "0917 555 0101")
            self.assertNotContains(response, "Contact (optional)")
            self.assertNotContains(response, "Removed players")

    def test_removed_players_are_listed_for_a_host_and_come_back(self):
        ben = self.club.member("Ben")
        self.assertNotContains(self.page(), "Removed players")
        groups.remove_member(self.host, ben.pk)
        response = self.page()
        self.assertContains(response, "Removed players (1)")
        self.assertContains(response, "Bring back")
        response = self.client.post(reverse("member_restore", args=[self.group.pk, ben.pk]), follow=True)
        self.assertRedirects(response, players_url(self.group) + "#players")
        self.assertContains(response, "Ben is back in the group.")
        self.assertNotContains(response, "Removed players")
        self.assertEqual(self.club.stats()["Ben"], (-50000, 1, 0))

    def test_a_restored_name_that_is_taken_says_the_new_name(self):
        ben = self.club.member("Ben")
        groups.remove_member(self.host, ben.pk)
        Member.objects.create(group=self.group, display_name="Ben")
        response = self.client.post(reverse("member_restore", args=[self.group.pk, ben.pk]), follow=True)
        self.assertContains(response, "Ben is back as Ben (2), because another Ben is in the group. Rename either one.")

    def test_several_names_are_added_or_none_and_the_typing_is_kept(self):
        url = reverse("member_add", args=[self.group.pk])
        self.assertContains(self.page(), "One name per line, up to 30.")
        response = self.client.post(url, {"names": "Carlo\n\n  Eli \r\nFe"}, follow=True)
        self.assertContains(response, "Added 3 players.")
        response = self.client.post(url, {"names": "Gio\nana\nGio"}, follow=True)
        self.assertContains(response, "Already in this group: ana.")
        self.assertContains(response, "Typed twice: Gio.")
        self.assertContains(response, "Gio\nana\nGio")
        self.assertFalse(Member.objects.filter(group=self.group, display_name="Gio").exists())
        response = self.client.post(url, {"names": "Gio"}, follow=True)
        self.assertContains(response, "Player added.")

    def test_host_actions_are_refused_for_a_player(self):
        ben = self.club.member("Ben")
        groups.remove_member(self.host, ben.pk)
        self.client.force_login(self.dani.user)
        self.assertEqual(self.client.post(reverse("member_restore", args=[self.group.pk, ben.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("member_add", args=[self.group.pk]), {"names": "X\nY"}).status_code, 403)

    def test_the_query_count_does_not_grow_with_players_or_removed_players(self):
        def count():
            from django.db import connection
            from django.test.utils import CaptureQueriesContext

            with CaptureQueriesContext(connection) as queries:
                self.page()
            return len(queries)

        before = count()
        added = groups.add_roster_players(self.host, [f"P{n}" for n in range(12)])
        for member in added[:6]:
            groups.remove_member(self.host, member.pk)
        self.assertEqual(count(), before)

    @override_settings(ROSTER_TOOLS=False)
    def test_switch_off_shows_the_section_as_it_was(self):
        groups.remove_member(self.host, self.club.member("Ben").pk)
        response = self.page()
        for gone in ("Removed players", "last played", "One name per line"):
            self.assertNotContains(response, gone)
        self.assertContains(response, "Add a player without a login")
        self.assertNotContains(self.player_page(self.host), "Change your name")
        response = self.player_page(self.dani)
        self.assertNotContains(response, "Contact (optional)")
        self.assertContains(response, reverse("member_remove", args=[self.group.pk, self.dani.pk]))
        response = self.client.post(reverse("member_remove", args=[self.group.pk, self.dani.pk]), follow=True)
        self.assertContains(response, "dani was removed.")
        self.assertNotContains(response, "Bring them back")
