from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from games import services
from games.models import SettingsPreset, Table
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_group, make_user

from .helpers import STAKES, make_preset, make_table


class PresetTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()

    def test_host_saves_a_preset_in_pesos_by_default(self):
        preset = make_preset(self.host)
        self.assertEqual((preset.default_buy_in, preset.unit), (100000, "php"))
        self.assertFalse(hasattr(preset, "chips_per_buy_in"))

    def test_rules_are_checked(self):
        bad = [
            {"small_blind": 3000},  # small blind above big blind
            {"min_buy_in": 150000},  # minimum above the usual buy-in
            {"max_buy_in": 50000, "min_buy_in": 50000},  # usual above maximum
            {"default_buy_in": 0, "min_buy_in": 0},
            {"big_blind": 20.5},  # never a float
        ]
        for overrides in bad:
            with self.assertRaises(RuleError, msg=overrides):
                make_preset(self.host, **overrides)
        self.assertEqual(SettingsPreset.objects.count(), 0)

    def test_database_checks_back_the_service(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            SettingsPreset.objects.create(group=self.group, name="bad", **{**STAKES, "min_buy_in": 300000})

    def test_duplicate_name_is_refused(self):
        make_preset(self.host)
        with self.assertRaises(RuleError):
            make_preset(self.host)

    def test_only_a_host_writes(self):
        ben = add_player(self.group, "ben")
        with self.assertRaises(NotAllowed):
            make_preset(ben)
        with self.assertRaises(NotAllowed):
            make_table(ben)

    def test_preset_of_another_group_cannot_be_edited(self):
        _, other_host = make_group("omar", "Other")
        preset = make_preset(other_host)
        with self.assertRaises(RuleError):
            services.save_preset(self.host, {"name": "x", "game_type": "nlh", **STAKES}, preset_id=preset.pk)


class TableTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()

    def test_seat_count_limits(self):
        self.assertEqual(make_table(self.host).seat_count, 9)
        for seats in (1, 13, "many"):
            with self.assertRaises(RuleError):
                make_table(self.host, name=f"T{seats}", seat_count=seats)
        with self.assertRaises(RuleError):
            make_table(self.host)  # duplicate name
        self.assertEqual(Table.objects.count(), 1)


class TablePresetViewTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")

    def test_host_creates_a_preset_with_peso_input(self):
        self.client.force_login(self.host.user)
        response = self.client.post(reverse("preset_create", args=[self.group.pk]), {
            "name": "10/20", "game_type": "nlh", "small_blind": "10", "big_blind": "20",
            "min_buy_in": "500", "max_buy_in": "2,000", "default_buy_in": "1000",
        })
        self.assertRedirects(response, reverse("group", args=[self.group.pk]))
        preset = SettingsPreset.objects.get()
        self.assertEqual((preset.max_buy_in, preset.small_blind), (200000, 1000))
        page = self.client.get(reverse("group", args=[self.group.pk]))
        self.assertContains(page, "buy-in ₱500–₱2,000 · usually ₱1,000")
        # Group rake shows both units even when this preset is pesos-only.
        self.assertNotContains(page, "usually 1,000 chips")

    def test_bad_amount_shows_an_error(self):
        self.client.force_login(self.host.user)
        response = self.client.post(reverse("preset_create", args=[self.group.pk]), {
            "name": "x", "game_type": "nlh", "small_blind": "10.005", "big_blind": "20",
            "min_buy_in": "500", "max_buy_in": "2000", "default_buy_in": "1000",
        })
        self.assertContains(response, "two decimal places")

    def test_player_and_stranger_are_refused(self):
        preset = make_preset(self.host)
        self.client.force_login(self.ben.user)
        self.assertEqual(self.client.get(reverse("preset_create", args=[self.group.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("table_create", args=[self.group.pk]), {"name": "T", "seat_count": 6}).status_code, 403)
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.get(reverse("preset_edit", args=[self.group.pk, preset.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("table_create", args=[self.group.pk]), {"name": "T", "seat_count": 6}).status_code, 404)
