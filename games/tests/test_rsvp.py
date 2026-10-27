"""RSVP: a host announces a session, players answer In or Out, the rest wait in line."""

import datetime
import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings

from audit.models import AuditEvent
from games import rsvp, services
from games.models import GameNight, Rsvp
from groups import services as groups_services
from groups.access import NotAllowed
from groups.errors import RuleError
from groups.models import Member
from groups.tests.helpers import add_player, make_group
from notify.models import Notice

from .helpers import make_session


def rid():
    return uuid.uuid4()


@override_settings(TABLE_NOTICES=True)
class RsvpTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.first = make_session(self.host, seat_count=4)
        self.night = self.first.night
        self.players = [add_player(self.group, name) for name in ("ana", "ben", "carlo", "dina", "emil")]
        self.ana, self.ben, self.carlo, self.dina, self.emil = self.players

    def announce(self, **kwargs):
        return services.announce_night(self.night.pk, self.host, **kwargs)

    def answer(self, member, going=True, actor=None):
        return services.answer_rsvp(self.night.pk, actor or member, member.pk, going, rid())

    def status(self, member):
        return Rsvp.objects.get(night=self.night, member=member).status

    def line(self):
        return [r.member for r in rsvp.waitlist(self.night)]

    # --- Announce --------------------------------------------------------------

    def test_announce_sets_the_limit_from_the_table_and_the_start_time(self):
        night = self.announce(start_time=datetime.time(20, 0))
        self.assertIsNotNone(night.announced_at)
        self.assertEqual((night.seat_limit, night.start_time), (4, datetime.time(20, 0)))
        self.assertTrue(AuditEvent.objects.filter(action="night.announced").exists())

    def test_announce_can_choose_the_seats(self):
        self.assertEqual(self.announce(seat_limit=6).seat_limit, 6)
        with self.assertRaises(RuleError):
            services.announce_night(make_session(self.host, table_name="Back table").night.pk, self.host, seat_limit=13)

    def test_announce_tells_every_member_with_a_login_but_the_host(self):
        self.announce()
        told = set(Notice.objects.filter(night_id=self.night.pk, kind="announced").values_list("user_id", flat=True))
        self.assertEqual(told, {p.user_id for p in self.players})

    def test_only_a_host_announces_and_only_once(self):
        with self.assertRaises(NotAllowed):
            services.announce_night(self.night.pk, self.ana)
        first = self.announce().announced_at
        self.assertEqual(self.announce().announced_at, first)  # a repeated tap
        self.assertEqual(Notice.objects.filter(night_id=self.night.pk).count(), len(self.players))

    # --- Answers ---------------------------------------------------------------

    def test_an_answer_needs_an_announced_session(self):
        with self.assertRaises(RuleError):
            self.answer(self.ana)

    def test_in_takes_a_seat_until_the_limit_then_joins_the_line(self):
        self.announce()
        for player in self.players:
            self.answer(player)
        self.assertEqual([self.status(p) for p in self.players], ["confirmed"] * 4 + ["waitlisted"])

    def test_out_from_a_seat_moves_the_first_in_line_up_and_tells_them(self):
        self.announce()
        for player in self.players:
            self.answer(player)
        self.answer(self.ben, going=False)
        self.assertEqual((self.status(self.ben), self.status(self.emil)), ("out", "confirmed"))
        self.assertTrue(Notice.objects.filter(user=self.emil.user, night_id=self.night.pk, kind="seated").exists())

    def test_out_then_in_again_joins_the_end_of_the_line(self):
        self.announce(seat_limit=2)
        for player in (self.ana, self.ben, self.carlo, self.dina):
            self.answer(player)
        self.answer(self.carlo, going=False)
        self.answer(self.carlo)
        self.assertEqual(self.line(), [self.dina, self.carlo])

    def test_a_repeated_in_changes_nothing(self):
        self.announce(seat_limit=2)
        for player in (self.ana, self.ben, self.carlo):
            self.answer(player)
        before = Rsvp.objects.get(night=self.night, member=self.carlo).queued_at
        self.answer(self.carlo)
        self.assertEqual(Rsvp.objects.get(night=self.night, member=self.carlo).queued_at, before)

    def test_the_same_request_is_recorded_once(self):
        self.announce()
        request_id = rid()
        services.answer_rsvp(self.night.pk, self.ana, self.ana.pk, True, request_id)
        services.answer_rsvp(self.night.pk, self.ana, self.ana.pk, False, request_id)  # replayed with other data
        self.assertEqual(self.status(self.ana), "confirmed")

    def test_a_player_answers_only_for_themselves(self):
        self.announce()
        with self.assertRaises(NotAllowed):
            self.answer(self.ben, actor=self.ana)

    def test_a_host_answers_for_a_roster_player_without_a_login(self):
        self.announce()
        roster = Member.objects.create(group=self.group, display_name="Fe")
        self.answer(roster, actor=self.host)
        row = Rsvp.objects.get(night=self.night, member=roster)
        self.assertEqual((row.status, row.answered_by), ("confirmed", self.host.user))

    def test_answers_stop_when_set_one_is_in_play(self):
        self.announce()
        services.transition(self.first.pk, self.host, "open")
        self.answer(self.ana)  # open: still counts
        services.transition(self.first.pk, self.host, "start")
        with self.assertRaises(RuleError):
            self.answer(self.ben)

    def test_an_archived_session_takes_no_answer(self):
        self.announce()
        GameNight.objects.filter(pk=self.night.pk).update(archived_at=datetime.datetime(2026, 10, 1, tzinfo=datetime.UTC))
        with self.assertRaises(RuleError):
            self.answer(self.ana)

    def test_a_member_of_another_group_cannot_answer_here(self):
        self.announce()
        _, other_host = make_group("zed", "Other")
        with self.assertRaises(RuleError):
            services.answer_rsvp(self.night.pk, other_host, other_host.pk, True, rid())

    # --- Seats -----------------------------------------------------------------

    def test_the_limit_cannot_go_under_the_confirmed_count(self):
        self.announce()
        for player in self.players[:3]:
            self.answer(player)
        with self.assertRaisesMessage(RuleError, "3 players are coming"):
            services.set_seat_limit(self.night.pk, self.host, 2)
        with self.assertRaises(RuleError):
            services.set_seat_limit(self.night.pk, self.host, 13)
        with self.assertRaises(NotAllowed):
            services.set_seat_limit(self.night.pk, self.ana, 6)

    def test_raising_the_limit_seats_the_line_in_order(self):
        self.announce(seat_limit=2)
        for player in self.players:
            self.answer(player)
        services.set_seat_limit(self.night.pk, self.host, 4)
        self.assertEqual(self.line(), [self.emil])
        self.assertEqual((self.status(self.carlo), self.status(self.dina)), ("confirmed", "confirmed"))

    def test_seat_now_seats_a_waiting_player_over_the_limit(self):
        self.announce(seat_limit=2)
        for player in (self.ana, self.ben, self.carlo, self.dina):
            self.answer(player)
        services.seat_from_waitlist(self.night.pk, self.host, self.dina.pk)
        self.night.refresh_from_db()
        self.assertEqual((self.status(self.dina), self.night.seat_limit, self.line()), ("confirmed", 3, [self.carlo]))

    def test_a_host_marks_a_confirmed_player_out_and_the_line_moves(self):
        self.announce(seat_limit=2)
        for player in (self.ana, self.carlo, self.ben):
            self.answer(player)
        self.answer(self.ana, going=False, actor=self.host)
        self.assertEqual((self.status(self.ana), self.status(self.ben)), ("out", "confirmed"))

    def test_each_write_bumps_the_sets_and_is_audited(self):
        self.announce()
        self.first.refresh_from_db()
        before = self.first.version
        self.answer(self.ana)
        self.first.refresh_from_db()
        self.assertEqual(self.first.version, before + 1)
        self.assertTrue(AuditEvent.objects.filter(action="rsvp.answered", session_id=self.first.pk).exists())

    # --- Removal ---------------------------------------------------------------

    def test_removing_a_confirmed_member_moves_the_line_up(self):
        self.announce(seat_limit=2)
        for player in (self.ana, self.carlo, self.ben):
            self.answer(player)
        groups_services.remove_member(self.host, self.ana.pk)
        self.assertEqual((self.status(self.ana), self.status(self.ben)), ("out", "confirmed"))

    # --- Database --------------------------------------------------------------

    def test_the_database_refuses_a_second_row_and_an_unknown_status(self):
        self.announce()
        self.answer(self.ana)
        row = Rsvp.objects.get(member=self.ana)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Rsvp.objects.create(night=self.night, member=self.ana, status="out", queued_at=row.queued_at,
                                answered_by=self.host.user)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Rsvp.objects.filter(pk=row.pk).update(status="maybe")


@override_settings(TABLE_NOTICES=True)
class RsvpReviewFixTests(TestCase):
    """The findings of the 2026-10-27 review, one test each."""

    def setUp(self):
        self.group, self.host = make_group()
        self.first = make_session(self.host, seat_count=4)
        self.night = self.first.night
        self.ana, self.ben, self.carlo = (add_player(self.group, n) for n in ("ana", "ben", "carlo"))
        services.announce_night(self.night.pk, self.host, seat_limit=2)
        for member in (self.ana, self.ben, self.carlo):
            services.answer_rsvp(self.night.pk, member, member.pk, True, rid())

    def test_a_session_with_answers_can_still_be_deleted(self):
        services.transition(self.first.pk, self.host, "cancel", "No game")
        services.delete_night(self.night.pk, self.host)
        self.assertFalse(Rsvp.objects.exists())

    def test_a_group_with_answers_can_still_be_deleted(self):
        services.transition(self.first.pk, self.host, "cancel", "No game")
        services.delete_group(self.host, self.group.name)
        self.assertFalse(Rsvp.objects.exists())

    def test_an_answer_alone_is_not_a_record_that_blocks_a_claim(self):
        self.assertFalse(groups_services._has_records(self.carlo))

    def test_seat_now_twice_returns_the_same_seat(self):
        first = services.seat_from_waitlist(self.night.pk, self.host, self.carlo.pk)
        again = services.seat_from_waitlist(self.night.pk, self.host, self.carlo.pk)
        self.assertEqual((first.pk, again.status), (again.pk, "confirmed"))

    def test_set_one_grows_with_the_seat_limit(self):
        services.set_seat_limit(self.night.pk, self.host, 6)
        self.first.refresh_from_db()
        self.assertEqual(self.first.seat_count, 6)
        services.set_seat_limit(self.night.pk, self.host, 3)
        self.first.refresh_from_db()
        self.assertEqual(self.first.seat_count, 6)  # never shrinks below what the table had

    def test_removal_locks_the_session_before_the_member(self):
        self.assertIn(services.lock_rsvp_nights, groups_services.REMOVE_LOCKS)
        self.assertIn(services.rsvp_member_removed, groups_services.REMOVED_HOOKS)
