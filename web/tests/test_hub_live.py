"""Your groups and a group's Sessions tab ask whether anything they show has changed (settlement.queries.hub_stamp)."""

import uuid

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from games import services as games
from games.tests.helpers import make_session
from groups import services as groups
from groups.tests.helpers import add_player, make_group, make_user
from ledger import services as ledger
from settlement import queries, services


class HubStampTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.seen = [queries.hub_stamp([self.group.pk])]

    def changed(self, what):
        now = queries.hub_stamp([self.group.pk])
        self.assertNotIn(now, self.seen, what)
        self.seen.append(now)

    def same(self, what):
        self.assertEqual(queries.hub_stamp([self.group.pk]), self.seen[-1], what)

    def test_it_follows_a_session_from_its_start_to_its_settling(self):
        self.same("a second read")
        session = make_session(self.host)
        self.changed("a session was created")
        games.transition(session.pk, self.host, "open")
        self.changed("its set was opened")
        a, b = (groups.add_roster_player(self.host, name) for name in "AB")
        self.changed("the roster grew")
        pa = games.add_participant(session.pk, self.host, a.pk)
        self.changed("a player sat down")
        pb = games.add_participant(session.pk, self.host, b.pk)
        games.transition(session.pk, self.host, "start", opening_buy_ins=False)
        self.changed("the set started")
        ledger.record_buy_in(session.pk, self.host, pa.pk, 100000, uuid.uuid4())
        ledger.record_buy_in(session.pk, self.host, pb.pk, 100000, uuid.uuid4())
        self.same("buy-ins are not on these pages")
        games.transition(session.pk, self.host, "end")
        self.changed("play ended")
        ledger.record_cash_out(session.pk, self.host, pa.pk, 150000, uuid.uuid4())
        ledger.record_cash_out(session.pk, self.host, pb.pk, 50000, uuid.uuid4())
        services.finalize(session.pk, self.host)
        self.changed("the set was finalized")
        plan = services.close_night(session.night_id, self.host)
        self.changed("the session closed")
        services.mark_paid(session.night_id, self.host, plan.transfers.get().pk, uuid.uuid4())
        self.changed("a transfer was marked paid")
        services.mark_unpaid(session.night_id, self.host, plan.transfers.get().pk)
        self.changed("the mark was undone")
        services.reopen_night(session.night_id, self.host, "why")
        self.changed("the session reopened")
        services.close_night(session.night_id, self.host)
        self.changed("closed again")
        games.archive_night(session.night_id, self.host)
        self.changed("the session was archived")

    def test_a_player_leaving_the_table_changes_it(self):
        session = make_session(self.host, state="open")
        member = groups.add_roster_player(self.host, "A")
        seat = games.add_participant(session.pk, self.host, member.pk)
        self.seen.append(queries.hub_stamp([self.group.pk]))
        games.withdraw_participant(session.pk, self.host, seat.pk)
        self.changed("a player was taken off the set")

    def test_another_group_does_not_move_it(self):
        _, other = make_group("olga", "Other Game")
        before = queries.hub_stamp([self.group.pk])
        make_session(other, state="open")
        self.assertEqual(queries.hub_stamp([self.group.pk]), before)
        self.assertNotEqual(queries.hub_stamp([self.group.pk, other.group_id]), before)


class HubStateViewTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.player = add_player(self.group, "Player")
        self.client.force_login(self.player.user)
        self.home, self.group_url = reverse("home_state"), reverse("group_state", args=[self.group.pk])

    def test_both_pages_say_where_to_ask_and_carry_no_stamp(self):
        home = self.client.get(reverse("home"))
        self.assertContains(home, f'data-state-url="{self.home}"')
        self.assertNotContains(home, "data-stamp")
        self.assertContains(home, 'name="turbo-refresh-method" content="morph"')
        page = self.client.get(reverse("group", args=[self.group.pk]))
        self.assertContains(page, f'data-state-url="{self.group_url}"')
        self.assertContains(page, 'name="turbo-refresh-method" content="morph"')

    def test_settings_and_stats_never_ask(self):
        self.client.force_login(self.host.user)
        for view in ("settings", "stats"):
            page = self.client.get(reverse("group", args=[self.group.pk]), {"view": view})
            self.assertNotContains(page, "data-state-url")
            self.assertNotContains(page, "turbo-refresh-method")

    def test_the_first_question_gets_the_stamp_and_then_nothing_new(self):
        for url in (self.home, self.group_url):
            first = self.client.get(url, {"v": ""})
            self.assertEqual(first.status_code, 200)
            stamp = first.json()["stamp"]
            self.assertEqual(self.client.get(url, {"v": stamp}).status_code, 204)
        make_session(self.host, state="open")
        for url in (self.home, self.group_url):
            answer = self.client.get(url, {"v": stamp})
            self.assertEqual(answer.status_code, 200)
            self.assertIn("no-store", answer["Cache-Control"])

    def test_home_covers_every_group_of_the_person_and_only_those(self):
        _, mine = make_group("olga", "Second Game")
        add_to = groups.add_roster_player(mine, "Someone")  # noqa: F841 - a change in a group the player is not in
        before = self.client.get(self.home, {"v": ""}).json()["stamp"]
        make_session(mine, state="open")
        self.assertEqual(self.client.get(self.home, {"v": before}).status_code, 204)
        make_session(self.host, state="open")
        self.assertEqual(self.client.get(self.home, {"v": before}).status_code, 200)

    def test_strangers(self):
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.get(self.group_url, {"v": ""}).status_code, 404)
        self.client.logout()
        self.assertEqual(self.client.get(self.group_url, {"v": ""}).status_code, 302)
        self.assertEqual(self.client.get(self.home, {"v": ""}).status_code, 302)

    def test_asking_is_cheap(self):
        for url in (self.home, self.group_url):
            stamp = self.client.get(url, {"v": ""}).json()["stamp"]
            with CaptureQueriesContext(connection) as made:
                self.client.get(url, {"v": stamp})
            self.assertLessEqual(len(made), 9, [q["sql"][:90] for q in made])
