import re

from django.test import TestCase
from django.urls import reverse

from games.tests.helpers import make_session, make_table
from groups.tests.helpers import add_player, make_group


class GroupViewTests(TestCase):
    """Sessions and group management are separate views of the one group route."""

    def setUp(self):
        self.group, self.host = make_group()
        self.url = reverse("group", args=[self.group.pk])
        self.client.force_login(self.host.user)

    def test_sessions_is_the_default_and_an_unknown_view_falls_back(self):
        for query in ({}, {"view": "nonsense"}):
            page = self.client.get(self.url, query)
            self.assertEqual(page.context["view"], "sessions")
            self.assertContains(page, 'aria-current="page"><span class="tab-marker" aria-hidden="true"></span>Sessions</a>')
            self.assertNotContains(page, "Invite players")
            self.assertNotContains(page, "rake-heading")

    def test_empty_stats_tab_is_visible_and_explains_what_is_needed(self):
        for user in (self.host.user, add_player(self.group, "viewer").user):
            self.client.force_login(user)
            self.assertContains(self.client.get(self.url), '?view=stats"')
            page = self.client.get(self.url, {"view": "stats"})
            self.assertContains(page, "No stats yet")
            self.assertContains(page, "Players appear here once a session closes.")
            self.assertContains(page, "Go to sessions")

    def test_empty_stats_still_requires_active_membership(self):
        other, stranger = make_group("Elsewhere")
        self.client.force_login(stranger.user)
        self.assertEqual(self.client.get(self.url, {"view": "stats"}).status_code, 404)

    def test_settings_holds_management_and_no_session_list(self):
        make_session(self.host, state="open")
        page = self.client.get(self.url, {"view": "settings"})
        self.assertContains(page, 'aria-current="page"><span class="tab-marker" aria-hidden="true"></span>Settings</a>')
        for heading in ("Tables", "Presets", "Chip presets", "Rake", "Group name", "Manage"):
            self.assertContains(page, f">{heading}</h2>")
        self.assertNotContains(page, "Current sessions")
        self.assertNotContains(page, "data-roster")
        self.assertNotContains(page, reverse("invite_create", args=[self.group.pk]))

    def test_players_holds_the_roster_with_invite_and_adding_first(self):
        page = self.client.get(self.url, {"view": "players"})
        self.assertContains(page, 'aria-current="page"><span class="tab-marker" aria-hidden="true"></span>Players</a>')
        html = page.content.decode()
        invite, add, roster = (html.index(mark) for mark in (reverse("invite_create", args=[self.group.pk]), reverse("member_add", args=[self.group.pk]), "data-roster"))
        self.assertLess(invite, add)
        self.assertLess(add, roster)
        self.assertNotContains(page, reverse("table_create", args=[self.group.pk]))

    def test_old_settings_addresses_of_players_still_arrive(self):
        """The server never sees "#players", so the Settings page itself says where they went."""
        page = self.client.get(self.url, {"view": "settings"})
        self.assertContains(page, f'id="players" class="notice notice-info settings-moved"><a href="{self.url}?view=players"')
        self.assertContains(page, f'id="invites" class="notice notice-info settings-moved"><a href="{self.url}?view=players#invites"')

    def test_a_player_is_not_told_about_invite_links(self):
        self.client.force_login(add_player(self.group, "viewer").user)
        self.assertNotContains(self.client.get(self.url, {"view": "settings"}), 'id="invites"')

    def test_empty_sessions_offer_one_next_action_for_the_role(self):
        page = self.client.get(self.url)
        self.assertContains(page, "Nobody is playing")
        self.assertNotContains(page, "Add a table")
        self.assertContains(page, "New session", count=1)
        make_table(self.host)
        page = self.client.get(self.url)
        self.assertContains(page, "New session", count=1)
        self.assertNotContains(page, "Add a table")
        self.client.force_login(add_player(self.group, "viewer").user)
        page = self.client.get(self.url)
        self.assertContains(page, "when a host starts it")
        self.assertNotContains(page, "New session")

    def test_new_session_sits_above_the_cards(self):
        make_session(self.host, state="open")
        html = self.client.get(self.url).content.decode()
        self.assertLess(html.index(reverse("session_create", args=[self.group.pk])), html.index('class="table-cards"'))
        self.client.force_login(add_player(self.group, "viewer").user)
        self.assertNotContains(self.client.get(self.url), "New session")

    def test_player_reads_players_without_host_forms(self):
        self.client.force_login(add_player(self.group, "viewer").user)
        page = self.client.get(self.url, {"view": "players"})
        self.assertContains(page, ">Players</h2>")
        self.assertNotContains(page, "<form method=\"post\" action=\"/g/")
        self.assertNotContains(page, "Invite players")

    def test_host_renames_the_group_from_settings(self):
        page = self.client.get(self.url, {"view": "settings"})
        self.assertContains(page, reverse("group_rename", args=[self.group.pk]))
        response = self.client.post(reverse("group_rename", args=[self.group.pk]), {"name": "Sunday Game"})
        self.assertRedirects(response, f"{self.url}?view=settings&open=name#name")
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Sunday Game")

    def test_settings_rows_come_in_order_and_closed(self):
        html = self.client.get(self.url, {"view": "settings"}).content.decode()
        ids = re.findall(r'<details class="settings-row" id="([a-z-]+)"( open)?', html)
        self.assertEqual(ids, [(row, "") for row in ("tables", "presets", "chip-presets", "rake", "name", "manage")])

    def test_a_player_has_no_group_name_or_manage_row(self):
        self.client.force_login(add_player(self.group, "viewer").user)
        html = self.client.get(self.url, {"view": "settings"}).content.decode()
        self.assertEqual(re.findall(r'<details class="settings-row" id="([a-z-]+)"', html), ["tables", "presets", "chip-presets", "rake"])

    def test_the_address_opens_the_row_it_names(self):
        page = self.client.get(self.url, {"view": "settings", "open": "presets"})
        self.assertContains(page, '<details class="settings-row" id="presets" open>')
        self.assertContains(page, '<details class="settings-row" id="tables">')

    def test_each_form_keeps_its_draft_in_its_open_row_after_a_refusal(self):
        cases = [
            ("group_rename", {"name": "   "}, "name", "This field is required."),
            ("table_create", {"name": "Kitchen", "seat_count": "99"}, "tables", 'value="Kitchen"'),
        ]
        for name, data, row, word in cases:
            with self.subTest(row=row):
                page = self.client.post(reverse(name, args=[self.group.pk]), data, follow=True)
                self.assertContains(page, f'<details class="settings-row" id="{row}" open>')
                self.assertContains(page, word)

    def test_a_refused_group_name_stays_with_its_form(self):
        self.client.post(reverse("group_rename", args=[self.group.pk]), {"name": "   "})
        page = self.client.get(self.url, {"view": "settings"})
        self.assertContains(page, "This field is required.")
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Friday Game")

    def test_a_player_cannot_rename_the_group(self):
        self.client.force_login(add_player(self.group, "viewer").user)
        self.assertNotContains(self.client.get(self.url, {"view": "settings"}), reverse("group_rename", args=[self.group.pk]))
        self.client.post(reverse("group_rename", args=[self.group.pk]), {"name": "Mine now"})
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Friday Game")

    def test_management_actions_return_to_their_tab_and_section(self):
        cases = [
            ("table_create", [self.group.pk], {"name": "Kitchen", "seat_count": "9"}, "settings", "tables"),
            ("member_add", [self.group.pk], {"name": "Ada"}, "players", "players"),
            ("invite_create", [self.group.pk], {}, "players", "invites"),
        ]
        for name, args, data, view, section in cases:
            with self.subTest(name=name):
                response = self.client.post(reverse(name, args=args), data)
                self.assertRedirects(response, f"{self.url}?view={view}" + (f"&open={section}" if view == "settings" else "") + f"#{section}")
