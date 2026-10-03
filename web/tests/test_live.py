from django.test import TestCase
from django.urls import reverse

from games import services as games
from groups.tests.helpers import make_user
from ledger.tests.helpers import Night


class LiveStateTests(TestCase):
    def setUp(self):
        self.night = Night("A", "B")
        self.ben = self.night.add_login_player("ben")
        self.url = reverse("session_state", args=[self.night.session.pk])
        self.client.force_login(self.ben.user)

    def test_unchanged_version_returns_204_with_no_body(self):
        response = self.client.get(self.url, {"v": self.night.refresh().version})
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.content, b"")

    def test_a_write_by_someone_else_returns_a_new_snapshot(self):
        seen = self.night.refresh().version
        self.night.buy("A", 1000)
        self.night.buy("B", 500)
        response = self.client.get(self.url, {"v": seen})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["version"], seen + 2)
        self.assertIn("₱1,500", data["html"])  # total bought in
        self.assertIn(">2<", data["html"])  # buy-in count
        self.assertEqual(self.client.get(self.url, {"v": data["version"]}).status_code, 204)

    def test_missing_or_stale_version_returns_the_full_state(self):
        for params in ({}, {"v": "garbage"}, {"v": "0"}):
            self.assertEqual(self.client.get(self.url, params).status_code, 200, params)

    def test_every_kind_of_write_bumps_the_version(self):
        session = self.night.session
        before = self.night.refresh().version
        buy_in = self.night.buy("A", 1000)
        from ledger import services as ledger
        ledger.reverse_buy_in(session.pk, self.night.host, buy_in.pk, "test")
        games.set_left(session.pk, self.night.host, self.night.players["B"].pk)
        games.transition(session.pk, self.night.host, "end")
        self.assertEqual(self.night.refresh().version, before + 4)

    def test_snapshot_respects_the_role(self):
        player_html = self.client.get(self.url).json()["html"]
        self.assertNotIn("Host controls", player_html)
        self.assertNotIn("buyins/add", player_html)
        self.client.force_login(self.night.host.user)
        host_html = self.client.get(self.url).json()["html"]
        self.assertIn("Host controls", host_html)
        self.assertIn("buyins/add", host_html)

    def test_non_member_gets_404_and_anonymous_is_sent_to_login(self):
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code, 302)

    def test_session_page_loads_the_polling_script(self):
        page = self.client.get(reverse("session", args=[self.night.session.pk]))
        self.assertContains(page, "js/live.js")
        self.assertContains(page, f'data-url="{self.url}"')
        self.assertContains(page, "Total bought in")
