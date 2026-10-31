"""The first table of a group is named on New session and made with the session, in one transaction."""
import datetime
import uuid

from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from games import services
from games.models import GameNight, Table
from games.tests.helpers import make_table
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_group


class FirstTableServiceTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()

    def create(self, actor=None, **options):
        return services.create_session(actor or self.host, {
            "table_name": "Rosa's kitchen", "game_date": datetime.date(2026, 10, 9), "game_type": "nlh", "unit": "php",
            "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 200000, "default_buy_in": 100000,
            **options,
        })

    def test_the_session_makes_its_table(self):
        session = self.create(table_seats=6)
        table = Table.objects.get(group=self.group)
        self.assertEqual((table.name, table.seat_count), ("Rosa's kitchen", 6))
        self.assertEqual((session.table, session.seat_count), (table, 6))
        self.assertTrue(AuditEvent.objects.filter(action="table.created").exists())

    def test_seats_default_to_nine(self):
        self.assertEqual(self.create().table.seat_count, 9)

    def test_a_retry_makes_one_table_and_one_session(self):
        request_id = uuid.uuid4()
        first = self.create(request_id=request_id)
        second = self.create(request_id=request_id)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Table.objects.filter(group=self.group).count(), 1)
        self.assertEqual(GameNight.objects.filter(group=self.group).count(), 1)

    def test_refused_stakes_leave_no_table(self):
        with self.assertRaises(RuleError):
            self.create(big_blind=500)  # below the small blind
        self.assertFalse(Table.objects.filter(group=self.group).exists())
        self.assertFalse(GameNight.objects.filter(group=self.group).exists())

    def test_a_refused_name_leaves_nothing(self):
        with self.assertRaises(RuleError):
            self.create(table_name="   ")
        self.assertFalse(Table.objects.filter(group=self.group).exists())

    def test_a_refused_seat_count_leaves_nothing(self):
        with self.assertRaises(RuleError):
            self.create(table_seats=40)
        self.assertFalse(Table.objects.filter(group=self.group).exists())
        self.assertFalse(GameNight.objects.filter(group=self.group).exists())

    def test_a_player_cannot_make_one(self):
        player = add_player(self.group, "ben")
        with self.assertRaises(NotAllowed):
            self.create(actor=player)
        self.assertFalse(Table.objects.filter(group=self.group).exists())

    def test_a_table_made_meanwhile_under_that_name_is_used(self):
        existing = make_table(self.host, name="Rosa's kitchen")
        self.assertEqual(self.create().table, existing)
        self.assertEqual(Table.objects.filter(group=self.group).count(), 1)

    def test_a_chosen_table_wins_over_a_typed_name(self):
        chosen = make_table(self.host, name="Garage")
        self.assertEqual(self.create(table_id=chosen.pk).table, chosen)
        self.assertEqual(Table.objects.filter(group=self.group).count(), 1)


class FirstTablePageTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.client.force_login(self.host.user)
        self.url = reverse("session_create", args=[self.group.pk])

    def form(self, **overrides):
        return {
            "request_id": str(uuid.uuid4()), "table_name": "Rosa's kitchen", "table_seats": "9", "game_date": "2026-10-09",
            "game_type": "nlh", "unit": "php", "small_blind": "10", "big_blind": "20",
            "min_buy_in": "500", "max_buy_in": "5000", "default_buy_in": "1000", "rake_mode": "off", **overrides,
        }

    def test_a_group_with_no_table_is_asked_for_its_name(self):
        html = self.client.get(self.url).content.decode()
        self.assertIn('name="table_name"', html)
        self.assertNotIn('name="table_id"', html)

    def test_a_group_with_a_table_chooses_it(self):
        make_table(self.host)
        html = self.client.get(self.url).content.decode()
        self.assertIn('name="table_id"', html)
        self.assertNotIn('name="table_name"', html)

    def test_sending_makes_the_table_and_the_session(self):
        response = self.client.post(self.url, self.form())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Table.objects.get(group=self.group).name, "Rosa's kitchen")
        self.assertTrue(GameNight.objects.filter(group=self.group).exists())

    def test_a_missing_name_is_refused_and_keeps_what_was_typed(self):
        response = self.client.post(self.url, self.form(table_name="", small_blind="15"))
        self.assertEqual(response.status_code, 422)
        self.assertContains(response, 'value="15"', status_code=422)
        self.assertFalse(Table.objects.filter(group=self.group).exists())

    def test_a_new_group_leads_straight_to_new_session(self):
        page = self.client.get(reverse("group", args=[self.group.pk])).content.decode()
        self.assertIn(f'href="{self.url}"', page)
        self.assertNotIn("Add a table", page)
        home = self.client.get(reverse("home")).content.decode()
        self.assertIn(f'href="{self.url}"', home)
        self.assertNotIn("Add a table", home)

    def test_a_player_of_a_new_group_is_not_offered_it(self):
        player = add_player(self.group, "ben")
        self.client.force_login(player.user)
        self.assertNotContains(self.client.get(reverse("group", args=[self.group.pk])), self.url)
        self.assertNotEqual(self.client.get(self.url).status_code, 200)
