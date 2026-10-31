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

    def test_a_person_with_no_session_yet_is_asked_later(self):
        self.log_in()
        self.assertContains(self.client.get(reverse("home")), "data-install-wait")

    def test_a_person_with_a_session_is_asked_now(self):
        from games.tests.helpers import make_session
        from groups.models import Member
        make_session(Member.objects.get(user__username="hana"))
        self.log_in()
        page = self.client.get(reverse("home"))
        self.assertContains(page, CAME_IN)
        self.assertNotContains(page, "data-install-wait")

    def test_an_archived_session_does_not_count(self):
        from games import services
        from games.tests.helpers import make_session
        from groups.models import Member
        hana = Member.objects.get(user__username="hana")
        session = make_session(hana)
        services.transition(session.pk, hana, "cancel")
        services.archive_night(session.night_id, hana)
        self.log_in()
        self.assertContains(self.client.get(reverse("home")), "data-install-wait")

    def test_a_player_is_asked_later_while_the_only_session_is_a_hidden_draft(self):
        from games import services
        from games.tests.helpers import make_session
        from groups.models import Member
        from groups.tests.helpers import add_player
        hana = Member.objects.get(user__username="hana")
        session = make_session(hana)
        ben = add_player(hana.group, "ben")
        self.client.force_login(ben.user)
        self.client.post(reverse("logout"))
        self.log_in("ben")
        self.assertContains(self.client.get(reverse("home")), "data-install-wait")
        self.client.post(reverse("logout"))
        services.transition(session.pk, hana, "open")
        self.log_in("ben")
        self.assertNotContains(self.client.get(reverse("home")), "data-install-wait")

    def test_a_removed_member_with_only_that_session_is_asked_later(self):
        from games.tests.helpers import make_session
        from groups.models import Member
        hana = Member.objects.get(user__username="hana")
        make_session(hana)
        Member.objects.filter(pk=hana.pk).update(status=Member.Status.REMOVED)
        self.log_in()
        self.assertContains(self.client.get(reverse("home")), "data-install-wait")

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
