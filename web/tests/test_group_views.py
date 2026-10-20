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
            self.assertNotContains(page, "Group rake account")

    def test_settings_holds_management_and_no_session_list(self):
        make_session(self.host, state="open")
        page = self.client.get(self.url, {"view": "settings"})
        self.assertContains(page, 'aria-current="page"><span class="tab-marker" aria-hidden="true"></span>Group settings</a>')
        for heading in ("Players", "Invite players", "Tables", "Presets", "Group rake account"):
            self.assertContains(page, f">{heading}</h2>")
        self.assertNotContains(page, "Current sessions")

    def test_empty_sessions_offer_one_next_action_for_the_role(self):
        page = self.client.get(self.url)
        self.assertContains(page, "Nobody is playing")
        self.assertContains(page, f'{self.url}?view=settings#tables">Add a table</a>')
        self.assertNotContains(page, "New session")
        make_table(self.host)
        page = self.client.get(self.url)
        self.assertContains(page, "New session", count=1)
        self.assertNotContains(page, "Add a table")
        self.client.force_login(add_player(self.group, "viewer").user)
        page = self.client.get(self.url)
        self.assertContains(page, "A host starts the next session")
        self.assertNotContains(page, "New session")

    def test_player_reads_settings_without_host_forms(self):
        self.client.force_login(add_player(self.group, "viewer").user)
        page = self.client.get(self.url, {"view": "settings"})
        self.assertContains(page, ">Players</h2>")
        # The one form a player has is for their own name.
        self.assertContains(page, "<form method=\"post\" action=\"/g/", count=1)
        self.assertContains(page, reverse("member_rename_self", args=[self.group.pk]))
        self.assertNotContains(page, "Invite players")

    def test_host_renames_the_group_from_settings(self):
        page = self.client.get(self.url, {"view": "settings"})
        self.assertContains(page, reverse("group_rename", args=[self.group.pk]))
        response = self.client.post(reverse("group_rename", args=[self.group.pk]), {"name": "Sunday Game"})
        self.assertRedirects(response, f"{self.url}?view=settings#manage")
        self.group.refresh_from_db()
        self.assertEqual(self.group.name, "Sunday Game")

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

    def test_management_actions_return_to_their_settings_section(self):
        cases = [
            ("table_create", [self.group.pk], {"name": "Kitchen", "seat_count": "9"}, "tables"),
            ("member_add", [self.group.pk], {"name": "Ada"}, "players"),
            ("invite_create", [self.group.pk], {}, "invites"),
        ]
        for name, args, data, section in cases:
            with self.subTest(name=name):
                response = self.client.post(reverse(name, args=args), data)
                self.assertRedirects(response, f"{self.url}?view=settings#{section}")
