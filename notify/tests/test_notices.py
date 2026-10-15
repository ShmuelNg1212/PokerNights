import uuid
from unittest import mock

from django.test import TestCase, override_settings

from games import services as games
from games.tests.helpers import make_session
from groups import services as groups
from groups.errors import RuleError
from groups.tests.helpers import add_player, make_group
from notify import services
from notify.models import Notice


class Table:
    """A host, a draft set and players with logins, for tests."""

    def __init__(self, state="setup"):
        self.group, self.host = make_group()
        self.session = make_session(self.host, state=state)

    def player(self, name):
        return add_player(self.group, name)

    def add(self, *members):
        return games.add_participants(self.session.pk, self.host, [m.pk for m in members], uuid.uuid4())

    def open(self):
        self.session = games.transition(self.session.pk, self.host, "open")

    def told(self):
        return {n.user.username: n for n in Notice.objects.filter(session_id=self.session.pk).select_related("user")}


@override_settings(TABLE_NOTICES=True)
class OpeningTellsTheAddedPlayersTests(TestCase):
    def test_opening_tells_each_added_player_with_a_login_and_nobody_else(self):
        table = Table()
        ana, ben = table.player("ana"), table.player("ben")
        nologin = groups.add_roster_player(table.host, "Cy")
        table.player("dee")  # in the group, not in the set
        table.add(ana, ben, nologin)
        self.assertEqual(table.told(), {})  # a draft tells nobody yet
        table.open()
        told = table.told()
        self.assertEqual(set(told), {"ana", "ben"})
        notice = told["ana"]
        self.assertEqual(notice.kind, "open")
        self.assertEqual(notice.title, "Friday table · set 1 is open")
        self.assertEqual(notice.body, "hana added you. Tap to see the table.")
        self.assertEqual(notice.url, f"/s/{table.session.pk}/")
        self.assertEqual(notice.actor_name, "hana")
        self.assertIsNone(notice.seen_at)

    def test_the_host_who_opens_is_not_told_about_their_own_seat(self):
        table = Table()
        games.add_participant(table.session.pk, table.host, table.host.pk)
        table.add(table.player("ana"))
        table.open()
        self.assertEqual(set(table.told()), {"ana"})

    def test_opening_closing_and_opening_again_tells_nobody_twice(self):
        table = Table()
        ana = table.player("ana")
        table.open()
        table.add(ana)  # told now: the set is open
        games.withdraw_participant(table.session.pk, table.host, table.session.participants.get(member=ana).pk)
        table.session = games.transition(table.session.pk, table.host, "close")
        table.add(ana)
        table.open()
        self.assertEqual(Notice.objects.filter(session_id=table.session.pk).count(), 1)

    def test_a_player_added_to_an_open_set_is_told_at_once(self):
        table = Table(state="open")
        table.add(table.player("ana"))
        notice = table.told()["ana"]
        self.assertEqual((notice.kind, notice.title), ("added", "Friday table · you’re in set 1"))
        self.assertEqual(notice.body, "hana added you. Tap to see the table.")

    def test_a_player_added_while_in_play_hears_that_play_has_started(self):
        table = Table(state="running")
        member = table.player("ana")
        games.add_participant(table.session.pk, table.host, member.pk)  # the one-player path
        notice = table.told()["ana"]
        self.assertEqual(notice.body, "hana added you. Play has started.")

    def test_a_player_who_joins_by_themselves_is_not_told(self):
        table = Table(state="open")
        ana = table.player("ana")
        games.add_participant(table.session.pk, ana, ana.pk)
        self.assertEqual(table.told(), {})

    def test_add_players_with_new_names_tells_only_the_ticked_players_with_logins(self):
        table = Table(state="open")
        ana = table.player("ana")
        games.add_players(table.session.pk, table.host, [ana.pk], "Ben\nCy", uuid.uuid4())
        self.assertEqual(set(table.told()), {"ana"})

    def test_a_refused_add_tells_nobody(self):
        table = Table(state="open")
        ana = table.player("ana")
        table.add(ana)
        Notice.objects.all().delete()
        with self.assertRaises(RuleError):
            table.add(ana, table.player("ben"))  # ana is already seated: nobody is added
        self.assertEqual(table.told(), {})

    def test_a_repeated_request_tells_nobody_twice(self):
        table = Table(state="open")
        ana, request_id = table.player("ana"), uuid.uuid4()
        games.add_participants(table.session.pk, table.host, [ana.pk], request_id)
        games.add_participants(table.session.pk, table.host, [ana.pk], request_id)
        self.assertEqual(Notice.objects.count(), 1)


class SwitchTests(TestCase):
    @override_settings(TABLE_NOTICES=False, PUSH_ALERTS=False)
    def test_with_both_switches_off_nothing_is_written(self):
        table = Table()
        table.add(table.player("ana"))
        table.open()
        self.assertEqual(table.told(), {})

    @override_settings(TABLE_NOTICES=False, PUSH_ALERTS=True, VAPID_PUBLIC_KEY="pub", VAPID_PRIVATE_KEY="priv")
    def test_with_push_on_the_notice_is_still_the_record_of_who_was_told(self):
        table = Table()
        table.add(table.player("ana"))
        with mock.patch("notify.push.send"):
            table.open()
        self.assertEqual(set(table.told()), {"ana"})
        self.assertEqual(services.unseen(table.told()["ana"].user, [table.session.pk]), {})  # but shown nowhere


@override_settings(TABLE_NOTICES=True)
class SeenTests(TestCase):
    def test_unseen_until_marked_seen_and_only_the_viewers_own(self):
        table = Table()
        ana, ben = table.player("ana"), table.player("ben")
        table.add(ana, ben)
        table.open()
        self.assertEqual(list(services.unseen(ana.user, [table.session.pk])), [table.session.pk])
        services.mark_seen(ana.user, table.session.pk)
        self.assertEqual(services.unseen(ana.user, [table.session.pk]), {})
        self.assertEqual(list(services.unseen(ben.user, [table.session.pk])), [table.session.pk])
