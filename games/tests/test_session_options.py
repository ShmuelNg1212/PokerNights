"""The New session options: a chip preset and an announcement, in the one transaction that creates the session."""
import datetime
import uuid

from django.test import TestCase, override_settings

from audit.models import AuditEvent
from games import services
from games.models import GameNight
from games.tests.helpers import make_table
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player, make_group
from notify.models import Notice

RED = [{"colour": "red", "label": "Small", "value": 2500}]


@override_settings(TABLE_NOTICES=True)
class SessionOptionTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")
        self.table = make_table(self.host, seat_count=7)

    def preset(self, unit="php", group_host=None, **overrides):
        data = {"name": f"Home {unit}", "unit": unit, "values": RED, **overrides}
        return services.save_chip_preset(group_host or self.host, data, uuid.uuid4())

    def create(self, actor=None, **options):
        return services.create_session(actor or self.host, {
            "table_id": self.table.pk, "game_date": datetime.date(2026, 10, 9), "game_type": "nlh", "unit": "php",
            "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 200000, "default_buy_in": 100000,
            **options,
        })

    def assert_nothing_made(self):
        self.assertFalse(GameNight.objects.exists())
        self.assertFalse(Notice.objects.exists())

    def test_without_options_the_session_has_no_values_and_stays_hidden(self):
        night = self.create().night
        self.assertEqual((night.chip_values, night.announced_at), ([], None))
        self.assertFalse(Notice.objects.exists())

    def test_a_chip_preset_gives_the_session_a_copy(self):
        preset = self.preset()
        night = self.create(chip_preset_id=preset.pk).night
        self.assertEqual(night.chip_values, [{"id": "red", "colour": "red", "label": "Small", "value": 2500}])
        self.assertEqual(night.chip_values_revision, 1)
        event = AuditEvent.objects.get(action="night.chip_values")
        self.assertEqual(event.data["preset"], "Home php")
        services.save_chip_preset(self.host, {"name": "Home php", "unit": "php", "values": [{"colour": "blue", "value": 5}]},
                                  uuid.uuid4(), preset_id=preset.pk)
        night.refresh_from_db()
        self.assertEqual(night.chip_values[0]["value"], 2500)

    def test_the_host_can_still_edit_the_copied_values(self):
        night = self.create(chip_preset_id=self.preset().pk).night
        services.set_chip_values(night.pk, self.host, [{"colour": "blue", "value": 5}], uuid.uuid4(), revision=1)
        night.refresh_from_db()
        self.assertEqual(night.chip_values[0]["colour"], "blue")

    def test_announcing_tells_the_group_and_takes_the_table_seats_and_the_start_time(self):
        night = self.create(announce=True, start_time=datetime.time(20, 30)).night
        self.assertIsNotNone(night.announced_at)
        self.assertEqual((night.seat_limit, night.start_time), (7, datetime.time(20, 30)))
        self.assertEqual(list(Notice.objects.values_list("user_id", "kind")), [(self.ben.user_id, "announced")])

    def test_both_options_together(self):
        night = self.create(announce=True, chip_preset_id=self.preset().pk).night
        self.assertIsNotNone(night.announced_at)
        self.assertEqual(len(night.chip_values), 1)

    def test_a_start_time_without_announcing_is_ignored(self):
        night = self.create(start_time=datetime.time(20, 30)).night
        self.assertIsNone(night.start_time)

    def test_a_repeated_request_tells_nobody_twice(self):
        request_id = uuid.uuid4()
        first = self.create(announce=True, request_id=request_id)
        again = self.create(announce=True, request_id=request_id)
        self.assertEqual(again.pk, first.pk)
        self.assertEqual(Notice.objects.count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action="night.announced").count(), 1)

    def test_a_preset_of_the_other_unit_creates_nothing(self):
        preset = self.preset(unit="chips", values=[{"colour": "red", "value": 25}])
        with self.assertRaisesMessage(RuleError, "chip preset"):
            self.create(announce=True, chip_preset_id=preset.pk)
        self.assert_nothing_made()

    def test_an_archived_preset_creates_nothing(self):
        preset = self.preset()
        services.archive_chip_preset(self.host, preset.pk, uuid.uuid4())
        with self.assertRaisesMessage(RuleError, "chip preset"):
            self.create(announce=True, chip_preset_id=preset.pk)
        self.assert_nothing_made()

    def test_a_preset_of_another_group_creates_nothing(self):
        _, other_host = make_group("other-host", "Other group")
        preset = self.preset(group_host=other_host)
        with self.assertRaisesMessage(RuleError, "chip preset"):
            self.create(announce=True, chip_preset_id=preset.pk)
        self.assert_nothing_made()

    def test_a_player_cannot_create_with_options(self):
        with self.assertRaises(NotAllowed):
            self.create(actor=self.ben, announce=True)
        self.assert_nothing_made()
