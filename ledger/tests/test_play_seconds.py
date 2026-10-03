"""Playing time is frozen with each result as it stood when play ended, not when the set was finalized."""

import datetime
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from games import services as games
from games.models import GameSession
from ledger.models import PlayerResult
from settlement import queries
from settlement import services as settlement

from .helpers import Night

BASE = datetime.datetime(2026, 10, 9, 12, 0, tzinfo=datetime.timezone.utc)


def at(minutes):
    return mock.patch("games.services.timezone.now", return_value=BASE + datetime.timedelta(minutes=minutes))


class PlaySecondsTests(TestCase):
    def play(self):
        with at(0):
            night = Night("A", "B")  # the helper starts the set
        night.buy("A", 1000)
        night.buy("B", 1000)
        with at(40):
            night.cash("B", 500, left=True)  # B goes home after 40 minutes
        with at(180):
            night.go("reconciliation")  # play ends after three hours
        night.cash("A", 1500)
        return night

    def test_result_stores_time_up_to_the_end_of_play(self):
        night = self.play()
        # Counting and finalizing take another fifty minutes. They add nothing.
        with mock.patch("django.utils.timezone.now", return_value=BASE + datetime.timedelta(minutes=230)):
            settlement.finalize(night.session.pk, night.host)
        seconds = dict(PlayerResult.objects.values_list("participant__member__display_name", "play_seconds"))
        self.assertEqual(seconds, {"A": 180 * 60, "B": 40 * 60})

    def test_results_and_session_page_show_it(self):
        night = self.play()
        settlement.finalize(night.session.pk, night.host)
        self.client.force_login(night.host.user)
        self.assertContains(self.client.get(reverse("session", args=[night.session.pk])), "played 3 h 00 min")
        self.assertContains(self.client.get(reverse("night", args=[night.session.night_id])), "played 40 min")
        standings = queries.night_outcome(night.session.night).standings
        self.assertEqual([s.play_seconds for s in standings], [10800, 2400])

    def test_session_time_is_the_sum_over_sets(self):
        night = self.play()
        settlement.finalize(night.session.pk, night.host)
        with at(240):
            second = games.start_next_set(night.session.night_id, night.host)
            games.transition(second.pk, night.host, "start")
        a = second.participants.get()
        import uuid
        from ledger import services as ledger
        ledger.record_buy_in(second.pk, night.host, a.pk, 100000, uuid.uuid4())
        with at(300):
            games.transition(second.pk, night.host, "end")
        ledger.record_cash_out(second.pk, night.host, a.pk, 100000, uuid.uuid4())
        settlement.finalize(second.pk, night.host)
        standings = {s.member.display_name: s.play_seconds for s in queries.night_outcome(night.session.night).standings}
        self.assertEqual(standings, {"A": (180 + 60) * 60, "B": 40 * 60})

    def test_set_without_recorded_time_stores_nothing(self):
        night = Night("A")
        night.buy("A", 1000)
        night.go("reconciliation")
        night.cash("A", 1000)
        night.session.play_periods.all().delete()  # as for a set played before timers existed
        night.session.play_intervals.all().delete()
        settlement.finalize(night.session.pk, night.host)
        self.assertIsNone(PlayerResult.objects.get().play_seconds)
        self.assertEqual(GameSession.objects.get().state, "finalized")
