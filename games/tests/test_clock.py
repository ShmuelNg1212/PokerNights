"""Each set has its own timer. Playing time comes from server timestamps only."""

import datetime
from contextlib import contextmanager
from unittest import mock

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from games import clock, services
from games.models import GameSession, Participant, PlayInterval, PlayPeriod
from groups import services as groups
from groups.tests.helpers import make_group

from .helpers import make_session

T0 = datetime.datetime(2026, 10, 9, 12, 0, tzinfo=datetime.timezone.utc)  # 8:00 PM in Manila
MIN = 60


def minute(n):
    return T0 + datetime.timedelta(minutes=n)


@contextmanager
def at(n):
    """Run the block as if the server clock showed ``T0 + n`` minutes."""
    with mock.patch("games.services.timezone.now", return_value=minute(n)):
        yield


class Table:
    """A set with named players, driven at chosen minutes."""

    def __init__(self, *names):
        self.group, self.host = make_group()
        self.game = make_session(self.host, state="open", seat_count=9)
        self.members = {name: groups.add_roster_player(self.host, name) for name in names}
        self.players = {}

    def join(self, name, when=None):
        with at(when if when is not None else 0):
            self.players[name] = services.add_participant(self.game.pk, self.host, self.members[name].pk)
        return self.players[name]

    def do(self, action, when):
        with at(when):
            self.game = services.transition(self.game.pk, self.host, action, "reason")

    def left(self, name, when, value=True):
        with at(when):
            services.set_left(self.game.pk, self.host, self.players[name].pk, value)

    def minutes(self, when):
        played = clock.player_seconds(self.game, minute(when))
        return {name: played.get(p.pk, 0) // MIN for name, p in self.players.items()}

    def set_minutes(self, when):
        return clock.set_seconds(self.game, minute(when)) // MIN


class SetTimerTests(TestCase):
    def setUp(self):
        self.table = Table("A", "B", "C", "D", "E", "F")
        for name in "ABCDEF":
            self.table.join(name)

    def test_nothing_is_timed_before_the_set_starts(self):
        self.assertIsNone(clock.set_seconds(self.table.game))
        self.assertEqual(PlayInterval.objects.count(), 0)

    def test_end_of_play_stops_every_timer_at_one_timestamp(self):
        self.table.do("start", 0)
        self.table.do("end", 180)  # 11:00 PM
        self.table.game.refresh_from_db()
        self.assertEqual(self.table.game.ended_at, minute(180))
        self.assertEqual(set(PlayInterval.objects.values_list("ended_at", flat=True)), {minute(180)})
        self.assertEqual(PlayPeriod.objects.get().ended_at, minute(180))
        self.assertEqual(PlayInterval.objects.count(), 6)

    def test_counting_time_adds_no_playing_time(self):
        self.table.do("start", 0)
        self.table.do("end", 180)
        at_end = (self.table.set_minutes(180), self.table.minutes(180))
        ten_minutes_later = (self.table.set_minutes(190), self.table.minutes(190))
        next_day = (self.table.set_minutes(180 + 24 * 60), self.table.minutes(180 + 24 * 60))
        self.assertEqual(at_end, (180, {name: 180 for name in "ABCDEF"}))
        self.assertEqual(ten_minutes_later, at_end)
        self.assertEqual(next_day, at_end)

    def test_the_timer_runs_while_the_set_runs(self):
        self.table.do("start", 0)
        self.assertEqual(self.table.set_minutes(25), 25)
        self.assertTrue(clock.is_running(self.table.game))
        self.table.do("end", 60)
        self.assertFalse(clock.is_running(self.table.game))

    def test_a_player_who_left_earlier_keeps_the_earlier_stop_time(self):
        self.table.do("start", 0)
        self.table.left("B", 45)
        self.table.do("end", 180)
        self.assertEqual(self.table.minutes(500)["B"], 45)
        self.assertEqual(PlayInterval.objects.get(participant=self.table.players["B"]).ended_at, minute(45))
        self.assertEqual(self.table.minutes(500)["A"], 180)

    def test_a_late_joiner_starts_late_and_a_returning_player_gets_a_second_interval(self):
        table = Table("A", "Late")
        table.join("A")
        table.do("start", 0)
        table.join("Late", when=30)
        table.left("A", 60)
        table.left("A", 90, value=False)  # back at the table half an hour later
        table.do("end", 120)
        self.assertEqual(table.minutes(999), {"A": 90, "Late": 90})
        self.assertEqual(PlayInterval.objects.filter(participant=table.players["A"]).count(), 2)
        self.assertEqual(table.set_minutes(999), 120)

    def test_resume_continues_the_set_timer_without_the_counting_time(self):
        self.table.do("start", 0)
        self.table.do("end", 60)
        self.table.do("resume", 80)  # twenty minutes of counting
        self.table.game.refresh_from_db()
        self.assertIsNone(self.table.game.ended_at)
        self.assertEqual(self.table.set_minutes(90), 70)
        self.table.do("end", 110)
        self.assertEqual(self.table.set_minutes(999), 90)
        self.assertEqual(self.table.minutes(999)["A"], 90)
        self.assertEqual(PlayPeriod.objects.count(), 2)
        self.table.game.refresh_from_db()
        self.assertEqual(self.table.game.ended_at, minute(110))

    def test_a_player_who_left_is_not_restarted_by_a_resume(self):
        self.table.do("start", 0)
        self.table.left("C", 30)
        self.table.do("end", 60)
        self.table.do("resume", 70)
        self.table.do("end", 100)
        self.assertEqual(self.table.minutes(999)["C"], 30)

    def test_no_player_time_exceeds_the_set_timer(self):
        self.table.do("start", 0)
        self.table.left("A", 10)
        self.table.left("A", 20, value=False)
        self.table.do("end", 50)
        self.table.do("resume", 60)
        self.table.do("end", 75)
        total = self.table.set_minutes(999)
        self.assertEqual(total, 65)
        self.assertTrue(all(minutes <= total for minutes in self.table.minutes(999).values()))

    def test_repeated_requests_change_nothing(self):
        self.table.do("start", 0)
        with at(5):
            clock.start(self.table.game, minute(5))  # a second start
            clock.open_interval(self.table.players["A"], minute(5))
        self.assertEqual((PlayPeriod.objects.count(), PlayInterval.objects.count()), (1, 6))
        self.table.do("end", 60)
        clock.stop(self.table.game, minute(75))  # a second end, later
        self.assertEqual(set(PlayInterval.objects.values_list("ended_at", flat=True)), {minute(60)})
        self.assertEqual(self.table.set_minutes(999), 60)

    def test_database_allows_one_running_timer_per_set_and_per_player(self):
        self.table.do("start", 0)
        with self.assertRaises(IntegrityError), transaction.atomic():
            PlayPeriod.objects.create(session=self.table.game, started_at=minute(1))
        with self.assertRaises(IntegrityError), transaction.atomic():
            PlayInterval.objects.create(session=self.table.game, participant=self.table.players["A"], started_at=minute(1))
        with self.assertRaises(IntegrityError), transaction.atomic():
            PlayPeriod.objects.filter(session=self.table.game).update(ended_at=minute(-5))

    def test_withdrawn_player_and_canceled_set_stop_their_timers(self):
        table = Table("A", "B")
        table.join("A")
        table.join("B")
        table.do("start", 0)
        with at(10):
            services.withdraw_participant(table.game.pk, table.host, table.players["B"].pk)
        table.do("cancel", 20)
        self.assertEqual(table.minutes(999), {"A": 20, "B": 10})
        self.assertFalse(clock.is_running(table.game))


class TimersBelongToTheirSetTests(TestCase):
    def test_each_set_has_its_own_timer_and_the_next_set_starts_at_zero(self):
        table = Table("A", "B")
        table.join("A")
        table.join("B")
        first = table.game
        table.do("start", 0)
        table.do("end", 60)
        with at(70):
            second = services.start_next_set(first.night_id, table.host)
        self.assertIsNone(clock.set_seconds(second))  # open, not started: nothing timed yet
        with at(75):
            second = services.transition(second.pk, table.host, "start")
        self.assertEqual(clock.set_seconds(second, minute(75)), 0)
        self.assertEqual(clock.set_seconds(second, minute(100)) // MIN, 25)
        before = list(PlayInterval.objects.filter(session=first).values_list("started_at", "ended_at"))
        with at(105):
            services.transition(second.pk, table.host, "end")
        # Ending set 2 changed no period or interval of set 1, and set 1 keeps its final value.
        self.assertEqual(list(PlayInterval.objects.filter(session=first).values_list("started_at", "ended_at")), before)
        self.assertEqual(clock.set_seconds(first, minute(999)) // MIN, 60)
        self.assertEqual(clock.set_seconds(second, minute(999)) // MIN, 30)
        self.assertEqual(GameSession.objects.get(pk=first.pk).ended_at, minute(60))


class ClockDisplayTests(TestCase):
    def test_format(self):
        self.assertEqual(clock.format_duration(None), "not recorded")
        self.assertEqual(clock.format_duration(59), "under 1 min")
        self.assertEqual(clock.format_duration(45 * 60), "45 min")
        self.assertEqual(clock.format_duration(65 * 60 + 30), "1 h 05 min")

    def test_pages_show_the_same_server_figure_on_every_load(self):
        table = Table("A")
        table.join("A")
        table.do("start", 0)
        table.do("end", 135)
        client = self.client
        client.force_login(table.host.user)
        for _ in range(2):  # a reload shows the same figure
            page = client.get(reverse("session", args=[table.game.pk]))
            self.assertContains(page, 'data-clock data-seconds="8100">2 h 15 min</span>')
            self.assertContains(page, "Play ended 10:15 PM")
            self.assertNotContains(page, "data-running")
        self.assertContains(client.get(reverse("night", args=[table.game.night_id])), "2 h 15 min")
        self.assertContains(client.get(reverse("session_log", args=[table.game.pk])), "Set timer")

    def test_running_set_marks_its_clock_as_running(self):
        table = Table("A")
        table.join("A")
        with mock.patch("games.services.timezone.now", return_value=timezone.now() - datetime.timedelta(minutes=10)):
            services.transition(table.game.pk, table.host, "start")
        self.client.force_login(table.host.user)
        page = self.client.get(reverse("session", args=[table.game.pk]))
        self.assertContains(page, "data-running>10 min</span>", count=2)  # the set timer and the player
        self.assertContains(page, "js/clock.js")

    def test_old_sets_show_not_recorded(self):
        table = Table("A")
        GameSession.objects.filter(pk=table.game.pk).update(state="reconciliation", started_at=T0, ended_at=minute(60))
        self.client.force_login(table.host.user)
        self.assertContains(self.client.get(reverse("session", args=[table.game.pk])), "not recorded")
        self.assertContains(self.client.get(reverse("session_log", args=[table.game.pk])), "Playing time was not recorded")
