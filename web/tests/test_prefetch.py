"""A page fetched ahead of a tap must not use up anything meant to be shown once."""

from django.test import TestCase
from django.urls import reverse

from games.tests.helpers import make_table
from groups.tests.helpers import make_group
from settlement.tests.test_archive import closed_example

PREFETCH = {"HTTP_X_SEC_PURPOSE": "prefetch"}


class PrefetchGuardTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.client.force_login(self.host.user)
        self.settings_url = reverse("group", args=[self.group.pk]) + "?view=settings"

    def test_a_flash_message_waits_for_the_real_page(self):
        make_table(self.host)
        self.client.post(reverse("table_create", args=[self.group.pk]), {"name": "Second table", "seat_count": "6"})
        ahead = self.client.get(reverse("home"), **PREFETCH)
        self.assertNotContains(ahead, "Table added.")       # not shown in a page nobody may see
        self.assertEqual(ahead["Cache-Control"], "no-store")
        again = self.client.get(reverse("home"), **PREFETCH)
        self.assertNotContains(again, "Table added.")
        real = self.client.get(self.settings_url)
        self.assertContains(real, "Table added.", count=1)  # shown once, on the page that is seen
        self.assertNotContains(self.client.get(self.settings_url), "Table added.")

    def test_a_kept_form_waits_for_the_real_page(self):
        make_table(self.host, name="Friday table")
        self.client.post(reverse("table_create", args=[self.group.pk]), {"name": "Friday table", "seat_count": "6"})
        self.client.get(self.settings_url, **PREFETCH)
        self.client.get(self.settings_url, **PREFETCH)
        real = self.client.get(self.settings_url)
        self.assertContains(real, "already exists")          # the refused name and its error are still there
        self.assertContains(real, 'value="Friday table"')

    def test_a_new_invite_link_waits_for_the_real_page(self):
        self.client.post(reverse("invite_create", args=[self.group.pk]))
        self.client.get(self.settings_url, **PREFETCH)
        real = self.client.get(self.settings_url)
        self.assertContains(real, "/join/")
        self.assertIsNotNone(real.context["new_invite_url"])

    def test_an_ordinary_request_is_untouched(self):
        self.client.post(reverse("invite_create", args=[self.group.pk]))
        first = self.client.get(self.settings_url)
        self.assertIsNotNone(first.context["new_invite_url"])
        self.assertIsNone(self.client.get(self.settings_url).context["new_invite_url"])  # shown once, as before
        self.assertNotIn("no-store", first.get("Cache-Control", ""))

    def test_a_prefetched_ledger_page_is_complete_and_never_stored(self):
        night = closed_example()
        self.client.force_login(night.host.user)
        page = self.client.get(reverse("night", args=[night.session.night_id]), **PREFETCH)
        self.assertContains(page, "Who pays whom")
        self.assertEqual(page["Cache-Control"], "no-store")

    def test_a_post_is_never_treated_as_a_prefetch(self):
        response = self.client.post(reverse("invite_create", args=[self.group.pk]), **PREFETCH)
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(self.client.get(self.settings_url).context["new_invite_url"])
