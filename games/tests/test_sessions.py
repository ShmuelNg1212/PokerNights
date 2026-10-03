import datetime

from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from games import services
from games.models import GameSession, SettingsVersion
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_group, make_user

from .helpers import STAKES, make_preset, make_session, make_table

State = GameSession.State


class CreateSessionTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()

    def test_session_starts_in_setup_with_settings_version_one(self):
        session = make_session(self.host)
        self.assertEqual(session.state, State.SETUP)
        self.assertEqual(session.seat_count, 9)
        self.assertEqual(session.unit, "php")
        version = services.current_settings(session)
        self.assertEqual((version.number, version.max_buy_in), (1, 200000))

    def test_table_must_belong_to_the_group(self):
        _, other_host = make_group("omar", "Other")
        other_table = make_table(other_host)
        with self.assertRaises(RuleError):
            services.create_session(self.host, {"table_id": other_table.pk, "game_date": datetime.date.today(), "game_type": "nlh", **STAKES})

    def test_only_a_host_creates(self):
        ben = add_player(self.group, "ben")
        with self.assertRaises(NotAllowed):
            make_session(ben)

    def test_editing_the_preset_later_changes_no_session(self):
        preset = make_preset(self.host)
        table = make_table(self.host, preset=preset)
        session = services.create_session(self.host, {
            "table_id": table.pk, "game_date": datetime.date(2026, 10, 9), "game_type": "nlh",
            "preset_id": preset.pk, **preset.stakes(),
        })
        services.save_preset(self.host, {"name": "10/20", "game_type": "nlh", **STAKES, "max_buy_in": 900000}, preset_id=preset.pk)
        self.assertEqual(services.current_settings(session).max_buy_in, 200000)


class LifecycleTests(TestCase):
    """Each action from each state, for a host and for a player."""

    ALLOWED = {
        ("setup", "open"): "open",
        ("setup", "cancel"): "canceled",
        ("open", "close"): "setup",
        ("open", "start"): "running",
        ("open", "cancel"): "canceled",
        ("running", "end"): "reconciliation",
        ("running", "cancel"): "canceled",
        ("reconciliation", "resume"): "running",
        ("reconciliation", "cancel"): "canceled",
    }

    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")
        self.table = make_table(self.host)

    def _session_in(self, state):
        if state in ("finalized", "canceled"):
            session = make_session(self.host, table=self.table)
            if state == "canceled":
                return services.transition(session.pk, self.host, "cancel")
            # Finalization has its own service; here only the resulting state matters.
            services.mark_finalized(session)
            return session
        return make_session(self.host, table=self.table, state=state)

    def test_every_state_and_action_for_a_host(self):
        for state in State.values:
            for action in services.TRANSITIONS:
                with self.subTest(state=state, action=action):
                    session = self._session_in(state)
                    expected = self.ALLOWED.get((state, action))
                    if expected is None:
                        with self.assertRaises(RuleError):
                            services.transition(session.pk, self.host, action, "reason")
                        session.refresh_from_db()
                        self.assertEqual(session.state, state)
                    else:
                        before = session.version
                        session = services.transition(session.pk, self.host, action, "reason")
                        self.assertEqual(session.state, expected)
                        self.assertEqual(session.version, before + 1)

    def test_a_player_can_do_no_transition(self):
        for state in ("setup", "open", "running", "reconciliation"):
            for action in services.TRANSITIONS:
                with self.subTest(state=state, action=action):
                    session = self._session_in(state)
                    with self.assertRaises(NotAllowed):
                        services.transition(session.pk, self.ben, action, "reason")

    def test_host_of_another_group_cannot_touch_the_session(self):
        _, other_host = make_group("omar", "Other")
        session = make_session(self.host, table=self.table)
        with self.assertRaises(RuleError):
            services.transition(session.pk, other_host, "open")

    def test_unknown_action_is_refused(self):
        session = make_session(self.host, table=self.table)
        with self.assertRaises(RuleError):
            services.transition(session.pk, self.host, "finalize")

    def test_cancel_after_setup_needs_a_reason(self):
        session = make_session(self.host, table=self.table, state="open")
        with self.assertRaises(RuleError):
            services.transition(session.pk, self.host, "cancel", "  ")
        session = services.transition(session.pk, self.host, "cancel", "Not enough players")
        self.assertEqual(session.cancel_reason, "Not enough players")

    def test_cancel_is_refused_while_money_is_in_the_session(self):
        session = make_session(self.host, table=self.table, state="running")

        def check(found):
            return found.pk == session.pk

        services.SESSION_MONEY_CHECKS.append(check)
        self.addCleanup(services.SESSION_MONEY_CHECKS.remove, check)
        with self.assertRaises(RuleError):
            services.transition(session.pk, self.host, "cancel", "reason")

    def test_each_transition_is_audited(self):
        session = make_session(self.host, table=self.table, state="running")
        actions = list(AuditEvent.objects.filter(session_id=session.pk).values_list("action", flat=True))
        self.assertEqual(actions, ["session.created", "session.open", "session.start"])
        session.refresh_from_db()
        self.assertIsNotNone(session.started_at)


class SettingsVersionTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()

    def test_a_change_adds_a_version_and_keeps_the_old_one(self):
        session = make_session(self.host, state="open")
        services.update_settings(session.pk, self.host, {**STAKES, "big_blind": 4000, "small_blind": 2000})
        numbers = list(SettingsVersion.objects.filter(session=session).values_list("number", "big_blind"))
        self.assertEqual(numbers, [(1, 2000), (2, 4000)])

    def test_same_values_add_no_version(self):
        session = make_session(self.host, state="open")
        services.update_settings(session.pk, self.host, dict(STAKES))
        self.assertEqual(session.settings_versions.count(), 1)

    def test_no_change_after_play_ends(self):
        session = make_session(self.host, state="reconciliation")
        with self.assertRaises(RuleError):
            services.update_settings(session.pk, self.host, {**STAKES, "big_blind": 4000})


class SessionViewTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")
        self.preset = make_preset(self.host)
        self.table = make_table(self.host, preset=self.preset)

    def test_host_creates_a_game_from_the_form(self):
        self.client.force_login(self.host.user)
        form_page = self.client.get(reverse("session_create", args=[self.group.pk]))
        self.assertContains(form_page, 'value="1000"')  # the preset's usual buy-in is filled in
        response = self.client.post(reverse("session_create", args=[self.group.pk]), {
            "table_id": self.table.pk, "game_date": "2026-10-09", "location": "Miguel's place", "game_type": "plo",
            "small_blind": "10", "big_blind": "20", "min_buy_in": "500",
            "max_buy_in": "2000", "default_buy_in": "1000",
            "preset_id": self.preset.pk,
        })
        session = GameSession.objects.get()
        self.assertRedirects(response, reverse("session", args=[session.pk]))
        self.assertEqual((session.game_type, session.location, str(session.game_date)), ("plo", "Miguel's place", "2026-10-09"))
        self.assertContains(self.client.get(reverse("session", args=[session.pk])), "Open for players")

    def test_draft_is_hidden_from_players_until_opened(self):
        session = make_session(self.host, table=self.table)
        self.client.force_login(self.ben.user)
        self.assertEqual(self.client.get(reverse("session", args=[session.pk])).status_code, 404)
        self.assertNotContains(self.client.get(reverse("group", args=[self.group.pk])), reverse("session", args=[session.pk]))
        services.transition(session.pk, self.host, "open")
        page = self.client.get(reverse("session", args=[session.pk]))
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, "Host controls")

    def test_player_and_stranger_cannot_post_transitions_or_settings(self):
        session = make_session(self.host, table=self.table, state="open")
        self.client.force_login(self.ben.user)
        self.assertEqual(self.client.post(reverse("session_transition", args=[session.pk]), {"action": "start"}).status_code, 403)
        self.assertEqual(self.client.get(reverse("session_settings", args=[session.pk])).status_code, 403)
        self.assertEqual(self.client.get(reverse("session_create", args=[self.group.pk])).status_code, 403)
        self.client.force_login(make_user("stranger"))
        for name in ("session", "session_settings"):
            self.assertEqual(self.client.get(reverse(name, args=[session.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("session_transition", args=[session.pk]), {"action": "start"}).status_code, 404)
        session.refresh_from_db()
        self.assertEqual(session.state, "open")

    def test_refused_transition_shows_a_message(self):
        session = make_session(self.host, table=self.table, state="open")
        self.client.force_login(self.host.user)
        response = self.client.post(reverse("session_transition", args=[session.pk]), {"action": "end"}, follow=True)
        self.assertContains(response, "not available")
