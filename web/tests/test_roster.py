"""Group settings → Players: the list, your own name, details, removing and bringing back, several names."""

import datetime

from django.test import TestCase, override_settings
from django.urls import reverse

from games.tests.test_add_players import Roster
from groups import services as groups
from groups.models import Member
from groups.tests.helpers import add_player, make_group
from settlement.tests.test_stats import OCT_1, Club


def settings_url(group):
    return reverse("group", args=[group.pk]) + "?view=settings"


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
        self.assertRedirects(response, settings_url(self.club.group) + "#players")
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
        return self.client.get(settings_url(self.group))

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

    def test_your_own_name(self):
        response = self.page()
        self.assertContains(response, "Change your name", count=1)
        self.assertContains(response, f"You still log in as <strong>{self.host.user.username}</strong>", html=False)
        url = reverse("member_rename_self", args=[self.group.pk])
        response = self.client.post(url, {"name": "Hana R"}, follow=True)
        self.assertContains(response, "Your name is now Hana R.")
        self.client.force_login(self.dani.user)
        self.assertContains(self.page(), "Change your name", count=1)
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
        response = self.page()
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
        self.assertRedirects(response, settings_url(self.group) + "#players")
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
        for gone in ("Change your name", "Contact (optional)", "Removed players", "last played", "One name per line"):
            self.assertNotContains(response, gone)
        self.assertContains(response, "Add a player without a login")
        self.assertContains(response, reverse("member_remove", args=[self.group.pk, self.dani.pk]))
        response = self.client.post(reverse("member_remove", args=[self.group.pk, self.dani.pk]), follow=True)
        self.assertContains(response, "dani was removed.")
        self.assertNotContains(response, "Bring them back")
