"""Start the set works from a draft: it records the opening and the start together."""
import uuid

from django.test import TestCase, override_settings
from django.urls import reverse

from audit.models import AuditEvent
from games import services
from games.models import GameSession
from games.tests.helpers import make_session
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_group
from ledger.models import BuyIn
from notify.models import Notice

State = GameSession.State


class StartFromDraftTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")
        self.session = make_session(self.host)

    def actions(self):
        return list(AuditEvent.objects.filter(session_id=self.session.pk, action__in=["session.open", "session.start"]).order_by("pk").values_list("action", flat=True))

    def seat(self):
        return services.add_participant(self.session.pk, self.host, self.ben.pk)

    def test_a_draft_starts_and_records_both_steps(self):
        self.seat()
        started = services.transition(self.session.pk, self.host, "start", request_id=uuid.uuid4())
        self.assertEqual(started.state, State.RUNNING)
        self.assertIsNotNone(started.started_at)
        self.assertEqual(self.actions(), ["session.open", "session.start"])

    def test_opening_buy_ins_are_recorded_as_from_an_open_set(self):
        self.seat()
        services.transition(self.session.pk, self.host, "start", request_id=uuid.uuid4())
        self.assertEqual([buy_in.amount for buy_in in BuyIn.objects.filter(session=self.session)], [100000])

    def test_the_host_can_decline_the_opening_buy_ins(self):
        self.seat()
        services.transition(self.session.pk, self.host, "start", request_id=uuid.uuid4(), opening_buy_ins=False)
        self.assertFalse(BuyIn.objects.filter(session=self.session).exists())

    def test_a_retry_changes_nothing(self):
        self.seat()
        request_id = uuid.uuid4()
        services.transition(self.session.pk, self.host, "start", request_id=request_id)
        services.transition(self.session.pk, self.host, "start", request_id=request_id)
        self.assertEqual(BuyIn.objects.filter(session=self.session).count(), 1)
        self.assertEqual(self.actions(), ["session.open", "session.start"])

    def test_a_set_with_no_player_starts_as_an_open_one_does(self):
        started = services.transition(self.session.pk, self.host, "start", request_id=uuid.uuid4())
        self.assertEqual(started.state, State.RUNNING)
        self.assertFalse(BuyIn.objects.filter(session=self.session).exists())

    def test_a_player_cannot_start_it(self):
        with self.assertRaises(NotAllowed):
            services.transition(self.session.pk, self.ben, "start", request_id=uuid.uuid4())
        self.session.refresh_from_db()
        self.assertEqual(self.session.state, State.SETUP)
        self.assertEqual(self.actions(), [])

    def test_a_running_set_cannot_start_again_under_a_new_request(self):
        services.transition(self.session.pk, self.host, "start", request_id=uuid.uuid4())
        with self.assertRaises(RuleError):
            services.transition(self.session.pk, self.host, "start", request_id=uuid.uuid4())

    def test_a_canceled_set_cannot_start(self):
        services.transition(self.session.pk, self.host, "cancel")
        with self.assertRaises(RuleError):
            services.transition(self.session.pk, self.host, "start", request_id=uuid.uuid4())

    def test_opening_still_works_alone(self):
        self.assertEqual(services.transition(self.session.pk, self.host, "open").state, State.OPEN)

    @override_settings(TABLE_NOTICES=True)
    def test_a_seated_player_is_told_as_when_a_set_opens(self):
        self.seat()
        Notice.objects.all().delete()
        services.transition(self.session.pk, self.host, "start", request_id=uuid.uuid4())
        self.assertTrue(Notice.objects.filter(user=self.ben.user).exists())


class StartFromDraftPageTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")
        self.session = make_session(self.host)
        self.client.force_login(self.host.user)
        self.url = reverse("session", args=[self.session.pk])

    def seat(self):
        services.add_participant(self.session.pk, self.host, self.ben.pk)

    def test_with_players_the_draft_offers_start_as_the_main_action(self):
        self.seat()
        html = self.client.get(self.url).content.decode()
        self.assertRegex(html, r'btn-primary[^>]*next-action[^>]*name="action" value="start"')
        self.assertIn('name="opening_buy_ins"', html)

    def test_letting_players_join_first_stays_as_a_quieter_action(self):
        self.seat()
        html = self.client.get(self.url).content.decode()
        self.assertRegex(html, r'class="btn[^"]*"[^>]*name="action" value="open">Let players join first')
        self.assertNotRegex(html, r'btn-primary[^>]*name="action" value="open"')

    def test_with_nobody_seated_the_main_action_is_add_players(self):
        html = self.client.get(self.url).content.decode()
        self.assertRegex(html, r'btn-primary[^"]*next-action[^>]*>Add players')
        self.assertNotRegex(html, r'btn-primary[^>]*name="action" value="start"')

    def test_sending_start_from_the_draft_runs_the_set(self):
        self.seat()
        self.client.post(reverse("session_transition", args=[self.session.pk]), {"action": "start", "request_id": str(uuid.uuid4()), "opening_buy_ins": "on"})
        self.session.refresh_from_db()
        self.assertEqual(self.session.state, State.RUNNING)
        self.assertEqual(BuyIn.objects.filter(session=self.session).count(), 1)
