import re

from django.test import TestCase
from django.urls import reverse

from ledger.tests.helpers import Night


class ScreenDepthTests(TestCase):
    """turbo-setup.js reads each screen's depth to choose a direction, and its hooks to carry a name or a chip."""

    def setUp(self):
        self.night = Night("Ana", "Ben")
        self.session = self.night.session
        self.group = self.night.group
        self.client.force_login(self.night.host.user)

    def main(self, url):
        html = self.client.get(url, follow=True).content.decode()
        return html, re.search(r'<main id="main"[^>]*>', html).group(0)

    def test_each_screen_says_how_deep_it_is(self):
        group = reverse("group", args=[self.group.pk])
        for url, depth in (
            (reverse("home"), 0), (group, 1), (group + "?view=settings", 1),
            (reverse("night", args=[self.session.night_id]), 2), (reverse("session_create", args=[self.group.pk]), 2),
            (reverse("session", args=[self.session.pk]), 3),
            (reverse("session_log", args=[self.session.pk]), 4), (reverse("session_settings", args=[self.session.pk]), 4),
            (reverse("participants_add", args=[self.session.pk]), 4),
        ):
            self.assertIn(f'data-depth="{depth}"', self.main(url)[1], url)

    def test_screens_outside_the_tree_have_no_depth(self):
        self.client.logout()
        self.assertNotIn("data-depth", self.main(reverse("login"))[1])

    def test_group_tabs_are_numbered_in_order(self):
        group = reverse("group", args=[self.group.pk])
        self.assertIn('data-tab="0"', self.main(group)[1])
        self.assertIn('data-tab="1"', self.main(group + "?view=stats")[1])
        self.assertIn('data-tab="2"', self.main(group + "?view=settings")[1])
        self.assertNotIn("data-tab", self.main(reverse("home"))[1])

    def test_one_heading_per_screen_can_carry_the_name(self):
        for url in (reverse("group", args=[self.group.pk]), reverse("night", args=[self.session.night_id]),
                    reverse("session", args=[self.session.pk])):
            self.assertEqual(self.main(url)[0].count('data-carry="title"'), 1, url)
        self.night.go("reconciliation")
        self.assertEqual(self.main(reverse("session", args=[self.session.pk]))[0].count('data-carry="title"'), 1)
        self.assertNotIn("data-carry", self.main(reverse("home"))[0])

    def test_cards_and_rows_have_what_the_script_looks_for(self):
        home = self.main(reverse("home"))[0]
        self.assertRegex(home, r'<article class="group-home"[^>]*>\s*<header class="group-home-head">\s*<h2 id="group-\d+"><a href="/g/\d+/">')
        sessions = self.main(reverse("group", args=[self.group.pk]))[0]
        self.assertRegex(sessions, rf'<a class="session-link" href="/n/{self.session.night_id}/">\s*<span class="grow"><strong>')

    def test_a_chip_names_its_player(self):
        html = self.main(reverse("session", args=[self.session.pk]))[0]
        for participant in self.night.players.values():
            self.assertEqual(html.count(f'data-m="{participant.member_id}"'), 1)

    def test_only_the_current_tab_has_the_marker_that_slides(self):
        group = reverse("group", args=[self.group.pk])
        for url in (group, group + "?view=settings"):
            html = self.main(url)[0]
            self.assertEqual(html.count('class="tab-marker"'), 1, url)
            self.assertIn('aria-current="page"><span class="tab-marker" aria-hidden="true"></span>', html)
