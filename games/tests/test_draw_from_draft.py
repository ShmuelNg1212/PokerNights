"""A host draws seats from a draft: the set opens and the seats are drawn in one transaction."""
import uuid

from django.test import TestCase, override_settings
from django.utils import timezone

from audit.models import AuditEvent
from games import services
from games.models import GameSession, SeatDraw
from games.tests.helpers import make_session
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_group
from notify.models import Notice

State = GameSession.State


@override_settings(TABLE_NOTICES=True)
class DrawFromDraftTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")
        self.cara = add_player(self.group, "cara")
        self.session = make_session(self.host)

    def seat(self, *members):
        for member in members:
            services.add_participant(self.session.pk, self.host, member.pk)

    def draw(self, request_id=None):
        return services.draw_seats(self.session.pk, self.host, request_id or uuid.uuid4())

    def state(self):
        self.session.refresh_from_db()
        return self.session.state

    def actions(self):
        return list(
            AuditEvent.objects.filter(session_id=self.session.pk, action__in=["session.open", "seats.drawn"])
            .order_by("pk").values_list("action", flat=True)
        )

    def test_a_draw_opens_the_draft_and_makes_one_current_draw(self):
        self.seat(self.host, self.ben, self.cara)
        draw = self.draw()
        self.assertEqual(self.state(), State.OPEN)
        self.assertEqual(SeatDraw.objects.filter(session=self.session, is_current=True).get().pk, draw.pk)
        self.assertEqual(draw.places.count(), 3)

    def test_the_log_has_the_opening_then_the_draw(self):
        self.seat(self.ben, self.cara)
        self.draw()
        self.assertEqual(self.actions(), ["session.open", "seats.drawn"])

    def test_the_version_rises_by_two(self):
        self.seat(self.ben, self.cara)
        self.session.refresh_from_db()
        before = self.session.version
        self.draw()
        self.session.refresh_from_db()
        self.assertEqual(self.session.version, before + 2)

    def test_seated_players_are_told_once_and_the_host_is_not(self):
        self.seat(self.host, self.ben, self.cara)
        self.draw()
        told = Notice.objects.filter(session_id=self.session.pk)
        self.assertEqual(sorted(told.values_list("user_id", flat=True)), sorted([self.ben.user_id, self.cara.user_id]))
        self.assertTrue(all("ready to join" in notice.title for notice in told))

    def test_a_replay_opens_and_draws_nothing_again(self):
        self.seat(self.ben, self.cara)
        key = uuid.uuid4()
        first = self.draw(key)
        self.session.refresh_from_db()
        version = self.session.version
        self.assertEqual(self.draw(key).pk, first.pk)
        self.session.refresh_from_db()
        self.assertEqual(self.session.version, version)
        self.assertEqual(SeatDraw.objects.filter(session=self.session).count(), 1)
        self.assertEqual(self.actions(), ["session.open", "seats.drawn"])
        self.assertEqual(Notice.objects.filter(session_id=self.session.pk).count(), 2)

    def test_one_player_is_refused_and_the_set_stays_a_draft(self):
        self.seat(self.ben)
        with self.assertRaisesMessage(RuleError, "at least two players"):
            self.draw()
        self.assertEqual(self.state(), State.SETUP)
        self.assertEqual(self.actions(), [])
        self.assertFalse(Notice.objects.filter(session_id=self.session.pk).exists())

    def test_a_refused_draw_after_the_opening_rolls_the_opening_back(self):
        # The open runs inside the draw's transaction, so a refusal after it leaves no trace.
        self.seat(self.ben, self.cara)
        original = services.transition

        def open_then_fail(*args, **kwargs):
            original(*args, **kwargs)
            raise RuleError("refused after the opening")

        with self.assertRaisesMessage(RuleError, "refused after the opening"):
            services.transition = open_then_fail
            try:
                self.draw()
            finally:
                services.transition = original
        self.assertEqual(self.state(), State.SETUP)
        self.assertEqual(self.actions(), [])
        self.assertFalse(Notice.objects.filter(session_id=self.session.pk).exists())

    @override_settings(SEAT_DRAW=False)
    def test_the_switch_refuses_and_the_set_stays_a_draft(self):
        self.seat(self.ben, self.cara)
        with self.assertRaisesMessage(RuleError, "switched off"):
            self.draw()
        self.assertEqual(self.state(), State.SETUP)

    def test_a_player_cannot_draw_on_a_draft(self):
        self.seat(self.ben, self.cara)
        with self.assertRaises(NotAllowed):
            services.draw_seats(self.session.pk, self.ben, uuid.uuid4())
        self.assertEqual(self.state(), State.SETUP)

    def test_a_running_set_is_still_refused(self):
        self.seat(self.ben, self.cara)
        services.transition(self.session.pk, self.host, "start", request_id=uuid.uuid4())
        with self.assertRaisesMessage(RuleError, "Seats are drawn before the set starts."):
            self.draw()
        self.assertFalse(SeatDraw.objects.filter(session=self.session).exists())

    def test_an_archived_session_is_refused(self):
        self.seat(self.ben, self.cara)
        night = self.session.night
        night.archived_at = timezone.now()
        night.save(update_fields=["archived_at"])
        with self.assertRaisesMessage(RuleError, "archived"):
            self.draw()
        self.assertEqual(self.state(), State.SETUP)
