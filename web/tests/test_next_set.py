"""The next set, for players: an ended set's page points to the session's next set, and the players
carried into it are told (table alerts)."""

from django.test import TestCase, override_settings
from django.urls import reverse

from games import services as games
from groups.tests.helpers import add_player
from ledger.tests.helpers import Night
from notify.models import Notice
from settlement import services as settlement


class Between:
    """Set 1 counting up with bea (a login) and roster players, and the host's Start next set."""

    def __init__(self, finalized=False, host_plays=False):
        self.night = Night("Ana", "Ben", state="running")
        self.bea = self.night.add_login_player("bea")
        if host_plays:
            games.add_participant(self.night.session.pk, self.night.host, self.night.host.pk)
        self.night.buy("Ana", 1000)
        self.night.go("reconciliation")
        if finalized:
            self.night.cash("Ana", 1000)
            settlement.finalize(self.night.session.pk, self.night.host)
        self.first = self.night.session

    def start(self):
        self.second = games.start_next_set(self.first.night_id, self.night.host)
        return self.second


@override_settings(TABLE_NOTICES=True)
class CarriedPlayersAreToldTests(TestCase):
    def test_each_carried_player_with_a_login_is_told_and_not_the_host(self):
        t = Between(host_plays=True)
        second = t.start()
        told = {n.user.username: n for n in Notice.objects.filter(session_id=second.pk).select_related("user")}
        self.assertEqual(set(told), {"bea"})
        notice = told["bea"]
        self.assertEqual(notice.kind, "next")
        self.assertEqual(notice.title, "Friday table · set 2 is open")
        self.assertEqual(notice.body, "hana started set 2. You’re at the table.")
        self.assertEqual(notice.url, f"/s/{second.pk}/")

    def test_a_player_who_left_set_one_is_not_carried_and_not_told(self):
        t = Between()
        p = t.first.participants.get(member=t.bea)
        games.set_left(t.first.pk, t.night.host, p.pk)
        second = t.start()
        self.assertFalse(Notice.objects.filter(session_id=second.pk).exists())

    def test_your_groups_says_who_started_the_set(self):
        t = Between()
        t.start()
        self.client.force_login(t.bea.user)
        self.assertContains(self.client.get(reverse("home")), "hana started set 2</p>")


class EndedSetPointsToTheNextTests(TestCase):
    def page(self, user, session):
        session.refresh_from_db()
        self.client.force_login(user)
        return self.client.get(reverse("session", args=[session.pk])).content.decode()

    def test_counting_up_page_shows_the_notice_for_a_carried_player_and_keeps_the_count(self):
        t = Between()
        second = t.start()
        page = self.page(t.bea.user, t.first)
        self.assertIn(f'<section class="next-set" data-next-set="{second.pk}"', page)
        self.assertIn("Set 2 has started", page)
        self.assertIn("You’re at the table.", page)
        self.assertIn(f'href="/s/{second.pk}/">Go to set 2</a>', page)
        self.assertIn(f'data-version="{t.first.version}.{second.pk}"', page)

    def test_a_member_not_at_the_new_table_is_told_to_join(self):
        t = Between()
        t.start()
        dee = add_player(t.night.group, "dee")
        self.assertIn("Join from the set.", self.page(dee.user, t.first))

    def test_the_poll_answers_with_the_notice_once_a_later_set_starts(self):
        t = Between()
        self.client.force_login(t.bea.user)
        url = reverse("session_state", args=[t.first.pk])
        t.first.refresh_from_db()
        before = str(t.first.version)
        self.assertEqual(self.client.get(url + "?v=" + before).status_code, 204)
        second = t.start()
        answer = self.client.get(url + "?v=" + before)
        self.assertEqual(answer.status_code, 200)
        self.assertEqual(answer.json()["version"], f"{before}.{second.pk}")
        self.assertIn("Set 2 has started", answer.json()["html"])
        self.assertEqual(self.client.get(url + f"?v={before}.{second.pk}").status_code, 204)

    def test_the_final_page_leads_to_the_next_set(self):
        t = Between(finalized=True)
        second = t.start()
        page = self.page(t.bea.user, t.first)
        self.assertIn(f'<a class="btn btn-block" href="/s/{second.pk}/">Go to set 2</a>', page)
        live = page.split('id="live"')[1].split("Full set log")[0]
        self.assertEqual(live.count("btn-primary"), 1)  # the notice's button is the one primary
        self.assertIn("Go to the session</a></p>", page)

    def test_a_canceled_next_set_is_not_pointed_to(self):
        t = Between()
        second = t.start()
        for p in second.participants.all():
            games.withdraw_participant(second.pk, t.night.host, p.pk)
        games.transition(second.pk, t.night.host, "cancel", "nobody stayed")
        page = self.page(t.bea.user, t.first)
        self.assertNotIn("has started", page)
        self.assertIn(f'data-version="{t.first.version}"', page)

    def test_a_set_in_play_asks_nothing_about_later_sets(self):
        t = Between()
        second = t.start()
        games.transition(second.pk, t.night.host, "start", opening_buy_ins=False)
        self.assertNotIn("data-next-set", self.page(t.bea.user, second))

    @override_settings(NEXT_SET_NOTICE=False)
    def test_the_switch_returns_the_page_to_before(self):
        t = Between(finalized=True)
        t.start()
        page = self.page(t.bea.user, t.first)
        self.assertNotIn("data-next-set", page)
        self.assertIn("Go to the session</a>", page)
        # No ".{later set}" part: the version is the set's own, then the session's states for its next step.
        self.assertIn(f'data-version="{t.first.version}:', page)
