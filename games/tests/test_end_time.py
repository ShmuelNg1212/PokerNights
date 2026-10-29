"""A host corrects a set's end time while it is counting up: earlier only, for the set and every player."""

import datetime
import uuid

from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from games import clock, services
from games.models import EndTimeCorrection, PlayInterval, PlayPeriod
from groups import services as groups
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player

from .test_clock import Table, at, minute


def correct(table, when, *, actor=None, request_id=None, reason=""):
    with at(300):  # the host corrects it later, while counting up
        return services.correct_end_time(
            table.game.pk, actor or table.host, minute(when), reason, request_id=request_id or uuid.uuid4(),
        )


class CorrectEndTimeTests(TestCase):
    def setUp(self):
        self.table = Table("A", "B", "C")
        for name in "ABC":
            self.table.join(name)
        self.table.do("start", 0)

    def ended(self, when=180):
        self.table.do("end", when)

    def test_shortens_the_set_and_every_player_at_the_table(self):
        self.ended(180)
        self.table.game = correct(self.table, 150)
        self.assertEqual(self.table.set_minutes(300), 150)
        self.assertEqual(self.table.minutes(300), {"A": 150, "B": 150, "C": 150})
        self.assertEqual(self.table.game.ended_at, minute(150))
        self.assertEqual(PlayPeriod.objects.get().ended_at, minute(150))

    def test_a_player_who_left_before_the_new_end_keeps_their_time(self):
        self.table.left("C", 60)
        self.ended(180)
        correct(self.table, 150)
        self.assertEqual(self.table.minutes(300), {"A": 150, "B": 150, "C": 60})

    def test_a_player_who_joined_after_the_new_end_gets_no_time(self):
        self.table.members["D"] = groups.add_roster_player(self.table.host, "D")
        self.table.join("D", 170)
        self.ended(180)
        correct(self.table, 150)
        self.assertEqual(self.table.minutes(300)["D"], 0)
        late = PlayInterval.objects.get(participant=self.table.players["D"])
        self.assertEqual((late.started_at, late.ended_at), (minute(150), minute(150)))

    def test_a_resumed_set_changes_only_its_last_period(self):
        self.table.do("end", 100)
        self.table.do("resume", 120)
        self.ended(200)
        correct(self.table, 180)
        periods = list(PlayPeriod.objects.values_list("started_at", "ended_at"))
        self.assertEqual(periods, [(minute(0), minute(100)), (minute(120), minute(180))])
        self.assertEqual(self.table.set_minutes(300), 160)
        self.assertEqual(self.table.minutes(300)["A"], 160)

    def test_records_the_correction_and_the_audit(self):
        self.ended(180)
        version = self.table.game.version
        game = correct(self.table, 150, reason="Forgot to tap")
        row = EndTimeCorrection.objects.get()
        self.assertEqual((row.old_ended_at, row.new_ended_at, row.reason), (minute(180), minute(150), "Forgot to tap"))
        event = AuditEvent.objects.filter(action="session.end_time").get()
        self.assertIn("10:30 PM", event.summary)
        self.assertIn("11:00 PM", event.summary)
        self.assertEqual(game.version, version + 1)

    def test_replaying_a_request_changes_nothing(self):
        self.ended(180)
        request_id = uuid.uuid4()
        correct(self.table, 150, request_id=request_id)
        game = correct(self.table, 120, request_id=request_id)
        self.assertEqual(game.ended_at, minute(150))
        self.assertEqual(EndTimeCorrection.objects.count(), 1)

    def test_a_second_correction_can_go_earlier_again(self):
        self.ended(180)
        correct(self.table, 150)
        correct(self.table, 140)
        self.assertEqual(self.table.set_minutes(300), 140)

    def test_refuses_a_time_at_or_after_the_recorded_end(self):
        self.ended(180)
        for when in (180, 200):
            with self.assertRaisesMessage(RuleError, "Choose a time before 11:00 PM"):
                correct(self.table, when)

    def test_refuses_a_time_at_or_before_the_last_start(self):
        self.table.do("end", 100)
        self.table.do("resume", 120)
        self.ended(200)
        for when in (120, 110):
            with self.assertRaisesMessage(RuleError, "Choose 10:01 PM or later."):
                correct(self.table, when)
        correct(self.table, 121)
        self.assertEqual(self.table.set_minutes(300), 101)

    def test_the_recorded_ends_minute_counts_as_unchanged(self):
        self.ended(180)
        PlayPeriod.objects.update(ended_at=minute(180) + datetime.timedelta(seconds=35))
        with self.assertRaisesMessage(RuleError, "Choose a time before 11:00 PM"):
            correct(self.table, 180)
        self.assertFalse(EndTimeCorrection.objects.exists())

    def test_refuses_while_the_set_is_in_play(self):
        with self.assertRaisesMessage(RuleError, "counting up"):
            correct(self.table, 30)

    def test_refuses_a_player(self):
        self.ended(180)
        player = self.table.members["A"]
        with self.assertRaises(NotAllowed):
            correct(self.table, 150, actor=player)
        self.assertEqual(clock.set_seconds(self.table.game, minute(300)), 180 * 60)


class EndTimeFormTests(TestCase):
    def setUp(self):
        self.table = Table("A", "B")
        for name in "AB":
            self.table.join(name)
        self.table.do("start", 0)
        self.table.do("end", 180)  # 11:00 PM in Manila
        self.url = reverse("session_end_time", args=[self.table.game.pk])

    def test_the_counting_page_offers_it_to_a_host(self):
        self.client.force_login(self.table.host.user)
        page = self.client.get(reverse("session", args=[self.table.game.pk]))
        self.assertContains(page, "Wrong end time?")
        self.assertContains(page, 'value="2026-10-09T23:00"')

    def test_a_host_sets_a_local_time(self):
        self.client.force_login(self.table.host.user)
        with at(300):
            response = self.client.post(self.url, {"ended_at": "2026-10-09T22:30", "request_id": str(uuid.uuid4())}, follow=True)
        self.table.game.refresh_from_db()
        self.assertEqual(self.table.game.ended_at, minute(150))
        self.assertContains(response, "End time set to 10:30 PM.")

    def test_a_time_with_seconds_is_taken_to_the_minute(self):
        self.client.force_login(self.table.host.user)
        with at(300):
            self.client.post(self.url, {"ended_at": "2026-10-09T22:30:45.000", "request_id": str(uuid.uuid4())})
        self.table.game.refresh_from_db()
        self.assertEqual(self.table.game.ended_at, minute(150))

    def test_the_fields_keep_what_the_host_typed_through_a_live_redraw(self):
        self.client.force_login(self.table.host.user)
        page = self.client.get(reverse("session", args=[self.table.game.pk]))
        self.assertContains(page, 'data-keep="end-time"')
        self.assertContains(page, 'data-keep="end-time-reason"')

    def test_a_time_that_is_not_a_date_is_refused(self):
        self.client.force_login(self.table.host.user)
        for typed in ("late", "2026-10-09T22:30+00:00"):
            response = self.client.post(self.url, {"ended_at": typed}, follow=True)
            self.assertContains(response, "Enter the date and time play ended.")
        self.assertFalse(EndTimeCorrection.objects.exists())

    def test_a_player_cannot_post_it(self):
        self.client.force_login(add_player(self.table.group, "bea").user)
        self.assertNotContains(self.client.get(reverse("session", args=[self.table.game.pk])), "Wrong end time?")
        response = self.client.post(self.url, {"ended_at": "2026-10-09T22:30"})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(EndTimeCorrection.objects.exists())
