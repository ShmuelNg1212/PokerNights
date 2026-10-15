"""Table alerts on the pages: the "added you" line on Your groups, the alerts panel, the worker's
push handlers and the set page's marks for a player who arrives on another phone."""

from django.test import TestCase, override_settings
from django.urls import reverse

from games import services as games
from notify.models import Notice
from notify.tests.test_notices import Table

KEYS = {"PUSH_ALERTS": True, "VAPID_PUBLIC_KEY": "BPublicKey", "VAPID_PRIVATE_KEY": "private"}


@override_settings(TABLE_NOTICES=True)
class AddedYouTests(TestCase):
    def setUp(self):
        self.table = Table()
        self.ana = self.table.player("ana")
        self.table.add(self.ana)
        self.table.open()
        self.client.force_login(self.ana.user)

    def test_the_card_says_who_added_the_player_and_its_button_leads(self):
        page = self.client.get(reverse("home")).content.decode()
        self.assertIn(f'<p class="band-added" data-added="{self.table.session.pk}"><span class="added-dot" aria-hidden="true"></span>hana added you</p>', page)
        self.assertIn('class="btn btn-primary btn-block" href="/s/%d/">Open set 1</a>' % self.table.session.pk, page)

    def test_opening_the_set_clears_it(self):
        self.client.get(reverse("session", args=[self.table.session.pk]))
        self.assertIsNotNone(Notice.objects.get(user=self.ana.user).seen_at)
        self.assertNotContains(self.client.get(reverse("home")), "added you")

    def test_a_set_in_play_keeps_the_line_and_a_canceled_set_loses_it(self):
        games.transition(self.table.session.pk, self.table.host, "start", opening_buy_ins=False)
        self.assertContains(self.client.get(reverse("home")), "hana added you")
        games.transition(self.table.session.pk, self.table.host, "cancel", "nobody came")
        self.assertNotContains(self.client.get(reverse("home")), "added you")

    def test_the_host_and_other_members_see_no_line(self):
        self.client.force_login(self.table.host.user)
        self.assertNotContains(self.client.get(reverse("home")), "added you")

    @override_settings(TABLE_NOTICES=False)
    def test_the_switch_hides_it(self):
        self.assertNotContains(self.client.get(reverse("home")), "added you")


class AlertsPanelTests(TestCase):
    def setUp(self):
        self.table = Table()
        self.client.force_login(self.table.host.user)

    @override_settings(**KEYS)
    def test_the_panel_carries_the_public_key_and_both_addresses_and_starts_hidden(self):
        page = self.client.get(reverse("home")).content.decode()
        self.assertIn('<section id="alerts" class="alerts-panel" hidden data-turbo-permanent data-alerts data-key="BPublicKey" data-subscribe="/alerts/subscribe/" data-unsubscribe="/alerts/unsubscribe/"', page)
        self.assertIn("Turn on table alerts", page)
        self.assertNotIn("private", page.split('id="alerts"')[1].split("</section>")[0])

    @override_settings(PUSH_ALERTS=True, VAPID_PUBLIC_KEY="BPublicKey", VAPID_PRIVATE_KEY="")
    def test_without_both_keys_there_is_no_panel(self):
        self.assertNotContains(self.client.get(reverse("home")), 'id="alerts"')

    @override_settings(SERVICE_WORKER=False, **KEYS)
    def test_without_the_worker_there_is_no_panel(self):
        self.assertNotContains(self.client.get(reverse("home")), 'id="alerts"')

    @override_settings(**{**KEYS, "PUSH_ALERTS": False})
    def test_the_switch_removes_the_panel(self):
        self.assertNotContains(self.client.get(reverse("home")), 'id="alerts"')


class WorkerTests(TestCase):
    def test_the_worker_shows_a_pushed_alert_and_opens_its_set(self):
        body = self.client.get("/sw.js").content.decode()
        self.assertIn('self.addEventListener("push"', body)
        self.assertIn("showNotification(data.title", body)
        self.assertIn('icon: "/static/icons/app-192.png"', body)
        self.assertIn('self.addEventListener("notificationclick"', body)
        self.assertIn("self.clients.openWindow(url)", body)

    @override_settings(SERVICE_WORKER=False)
    def test_the_remover_has_no_push_handler(self):
        self.assertNotIn('"push"', self.client.get("/sw.js").content.decode())


class SetPageMarksTests(TestCase):
    def setUp(self):
        self.table = Table(state="open")
        self.ana = self.table.player("ana")
        self.table.add(self.ana)
        self.client.force_login(self.ana.user)

    def test_rows_carry_the_name_and_the_viewers_own_row_says_so(self):
        page = self.client.get(reverse("session", args=[self.table.session.pk])).content.decode()
        self.assertIn('data-arrivals="on"', page)
        self.assertIn('<p id="arrival-news" class="visually-hidden" aria-live="polite"></p>', page)
        self.assertIn('data-name="ana" data-mine>', page)
        self.assertIn('data-player-count="1"', page)

    def test_the_poll_snapshot_carries_them_too(self):
        snapshot = self.client.get(reverse("session_state", args=[self.table.session.pk]) + "?v=0").json()
        self.assertIn('data-name="ana" data-mine>', snapshot["html"])

    @override_settings(ARRIVAL_MARKS=False)
    def test_the_switch_leaves_the_page_unmarked(self):
        self.assertNotContains(self.client.get(reverse("session", args=[self.table.session.pk])), "data-arrivals")
