"""The suggestion to put the app on the home screen: when the server says "this person just came in"."""

import json
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from groups.tests.helpers import make_group, make_user

CAME_IN = "data-came-in"
SHEET = 'id="install-sheet"'


class CameInTests(TestCase):
    def log_in(self, name="hana"):
        return self.client.post(reverse("login"), {"username": name, "password": "tablestakes-91"})

    def setUp(self):
        make_group()

    def test_the_first_page_after_a_login_says_so_and_only_that_one(self):
        self.assertEqual(self.log_in().status_code, 302)
        first = self.client.get(reverse("home"))
        self.assertContains(first, CAME_IN)
        self.assertContains(first, SHEET)
        second = self.client.get(reverse("home"))
        self.assertNotContains(second, CAME_IN)
        self.assertContains(second, SHEET)  # the sheet is there to be opened from Your groups

    def test_every_login_says_so_again(self):
        self.log_in()
        self.client.get(reverse("home"))
        self.client.post(reverse("logout"))
        self.log_in()
        self.assertContains(self.client.get(reverse("home")), CAME_IN)

    def test_a_page_fetched_ahead_of_a_tap_does_not_use_it_up(self):
        self.log_in()
        ahead = self.client.get(reverse("home"), headers={"X-Sec-Purpose": "prefetch"})
        self.assertNotContains(ahead, CAME_IN)
        self.assertContains(self.client.get(reverse("home")), CAME_IN)

    @override_settings(DOOR_MOTION=False)
    def test_it_does_not_depend_on_the_arrival_motion(self):
        self.log_in()
        page = self.client.get(reverse("home"))
        self.assertContains(page, CAME_IN)
        self.assertNotContains(page, "data-welcome")

    @override_settings(INSTALL_PROMPT=False)
    def test_switch_off(self):
        self.log_in()
        page = self.client.get(reverse("home"))
        for text in (CAME_IN, SHEET, "data-install-open", "data-app-link"):
            self.assertNotContains(page, text)
        self.assertContains(page, "data-welcome")  # the arrival is untouched

    def test_a_signed_out_page_has_no_sheet(self):
        page = self.client.get(reverse("login"))
        self.assertNotContains(page, SHEET)
        self.assertNotContains(page, CAME_IN)

    def test_your_groups_holds_the_way_back_and_the_link_field(self):
        self.client.force_login(make_user("solo"))  # no group yet: the first-group screen
        for user in ("solo", "hana"):
            self.client.force_login(type(self).user(user))
            page = self.client.get(reverse("home"))
            self.assertContains(page, "data-install-open")
            self.assertContains(page, "data-app-link")

    @staticmethod
    def user(name):
        from django.contrib.auth import get_user_model

        return get_user_model().objects.get(username=name)


class ManifestLinkTests(TestCase):
    def test_an_installed_app_takes_its_own_links(self):
        manifest = json.loads((Path(settings.BASE_DIR) / "static" / "manifest.webmanifest").read_text())
        self.assertEqual(manifest["scope"], "/")
        self.assertEqual(manifest["launch_handler"], {"client_mode": ["navigate-existing", "auto"]})
        self.assertEqual(manifest["handle_links"], "preferred")
