"""A session (GameNight) holds sets (GameSession), played one after another."""

from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from games import services
from games.models import GameNight, GameSession, SettingsVersion
from groups.errors import RuleError
from groups.tests.helpers import add_player, make_group, make_user

from .helpers import CHIP_STAKES, make_session


def second_set(first, state="open"):
    """A second set in the same session, made directly. Task 2 adds the real action."""
    new = GameSession.objects.create(
        night=first.night, set_number=2, group=first.group, table=first.table, game_date=first.game_date,
        unit=first.unit, seat_count=first.seat_count, created_by=first.created_by, state=state,
    )
    SettingsVersion.objects.create(
        session=new, number=1, created_by=first.created_by, **services.current_settings(first).stakes()
    )
    return new


class NightTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()

    def test_creating_a_game_creates_a_session_with_set_one(self):
        first = make_session(self.host, unit="chips", **CHIP_STAKES)
        night = first.night
        self.assertEqual((first.set_number, night.sets.count(), night.status), (1, 1, "open"))
        self.assertEqual((night.table, night.game_date, night.unit, night.location), (first.table, first.game_date, "chips", "Miguel's place"))
        self.assertIn("set 1", str(first))

    def test_only_one_set_of_a_session_can_be_in_play(self):
        first = make_session(self.host, state="running")
        for state in ("setup", "open", "running"):
            with self.assertRaises(IntegrityError), transaction.atomic():
                second_set(first, state=state)
        services.transition(first.pk, self.host, "end")
        second_set(first)  # play of set 1 has ended: allowed
        with self.assertRaises(IntegrityError), transaction.atomic():
            GameSession.objects.filter(pk=first.pk).update(state="running")

    def test_set_numbers_are_unique_in_a_session(self):
        first = make_session(self.host, state="reconciliation")
        second_set(first)
        with self.assertRaises(IntegrityError), transaction.atomic():
            second_set(first, state="finalized")

    def test_unit_cannot_change_once_a_session_has_several_sets(self):
        first = make_session(self.host, state="reconciliation")
        second = second_set(first)
        with self.assertRaisesMessage(RuleError, "several sets"):
            services.update_settings(second.pk, self.host, {**CHIP_STAKES, "unit": "chips"})

    def test_unit_change_of_a_single_set_also_changes_the_session(self):
        first = make_session(self.host, state="open")
        services.update_settings(first.pk, self.host, {**CHIP_STAKES, "unit": "chips"})
        self.assertEqual(GameNight.objects.get(pk=first.night_id).unit, "chips")


class NightPageTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")
        self.first = make_session(self.host)
        self.url = reverse("night", args=[self.first.night_id])

    def test_session_page_lists_its_sets(self):
        services.transition(self.first.pk, self.host, "open")
        services.transition(self.first.pk, self.host, "start")
        services.transition(self.first.pk, self.host, "end")
        second = second_set(self.first)
        self.client.force_login(self.ben.user)
        page = self.client.get(self.url)
        for text in ("Set 1", "Set 2", "Counting up", reverse("session", args=[self.first.pk]), reverse("session", args=[second.pk]), "Open set 2"):
            self.assertContains(page, text)
        self.assertContains(self.client.get(reverse("session", args=[second.pk])), "Set 2")

    def test_draft_session_is_hidden_from_players_and_strangers(self):
        self.client.force_login(self.ben.user)
        self.assertEqual(self.client.get(self.url).status_code, 404)
        self.assertNotContains(self.client.get(reverse("group", args=[self.group.pk])), self.url)
        self.client.force_login(self.host.user)
        self.assertContains(self.client.get(reverse("group", args=[self.group.pk])), self.url)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        services.transition(self.first.pk, self.host, "open")
        self.client.force_login(self.ben.user)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_set_page_links_back_to_its_session(self):
        self.client.force_login(self.host.user)
        self.assertContains(self.client.get(reverse("session", args=[self.first.pk])), self.url)


class NightMigrationTests(TransactionTestCase):
    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_each_existing_game_becomes_a_session_with_one_set(self):
        import datetime

        executor = MigrationExecutor(connection)
        executor.migrate([("games", "0005_participantbatch")])
        old = executor.loader.project_state([("games", "0005_participantbatch")]).apps
        user = old.get_model("accounts", "User").objects.create(username="h")
        group = old.get_model("groups", "GameGroup").objects.create(name="G", created_by=user)
        table = old.get_model("games", "Table").objects.create(group=group, name="T", seat_count=9)
        Game = old.get_model("games", "GameSession")
        ids = {
            state: Game.objects.create(
                group=group, table=table, game_date=datetime.date(2026, 10, 3), location="Here", unit="chips",
                state=state, seat_count=9, created_by=user,
            ).pk
            for state in ("running", "reconciliation", "finalized", "canceled")
        }
        target = [("games", "0007_gamenight_night_group_status_date_and_more")]
        executor = MigrationExecutor(connection)
        executor.migrate(target)
        new = executor.loader.project_state(target).apps
        Night, Set = new.get_model("games", "GameNight"), new.get_model("games", "GameSession")
        self.assertEqual(Night.objects.count(), 4)
        for state, pk in ids.items():
            game = Set.objects.get(pk=pk)
            night = Night.objects.get(pk=game.night_id)
            self.assertEqual((game.set_number, Set.objects.filter(night_id=night.pk).count()), (1, 1))
            self.assertEqual((night.unit, night.location, night.table_id), ("chips", "Here", table.pk))
            self.assertEqual(night.status, "closed" if state in ("finalized", "canceled") else "open", state)
