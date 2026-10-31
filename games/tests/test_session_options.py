"""The New session options: a chip preset and an announcement, in the one transaction that creates the session."""
import datetime
import uuid

from django.test import TestCase, override_settings
from django.urls import reverse

from audit.models import AuditEvent
from games import services
from games.models import GameNight
from games.tests.helpers import make_preset, make_session, make_table
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


@override_settings(TABLE_NOTICES=True)
class NewSessionOptionFormTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")
        self.table = make_table(self.host)
        self.url = reverse("session_create", args=[self.group.pk])
        self.client.force_login(self.host.user)

    def preset(self, name="Home set", unit="php"):
        return services.save_chip_preset(self.host, {"name": name, "unit": unit, "values": RED}, uuid.uuid4())

    def post(self, **options):
        return self.client.post(self.url, {
            "table_id": self.table.pk, "game_date": "2026-10-09", "game_type": "nlh", "unit": "php", "small_blind": "10",
            "big_blind": "20", "min_buy_in": "500", "max_buy_in": "2000", "default_buy_in": "1000", **options,
        })

    def test_the_form_offers_both_options_off(self):
        preset = self.preset()
        chips = self.preset("Chip set", "chips")
        page = self.client.get(self.url).content.decode()
        self.assertIn('<option value="" selected>Set later</option>', page)
        self.assertIn(f'<option value="{preset.pk}" data-unit="php">Home set</option>', page)
        self.assertIn(f'<option value="{chips.pk}" data-unit="chips">Chip set (Chips)</option>', page)
        self.assertRegex(page, r'<input type="checkbox" name="announce" id="id_announce">')
        self.assertIn("1 player with a login gets a notice.", page)

    def test_a_group_without_chip_presets_sees_no_chip_field(self):
        self.assertNotContains(self.client.get(self.url), 'name="chip_preset_id"')

    def test_ticking_announce_tells_the_group_and_says_so(self):
        response = self.post(announce="on", start_time="20:30")
        night = GameNight.objects.get()
        self.assertRedirects(response, reverse("night", args=[night.pk]), fetch_redirect_response=False)
        self.assertEqual(night.start_time, datetime.time(20, 30))
        self.assertEqual(Notice.objects.filter(user=self.ben.user, night_id=night.pk, kind="announced").count(), 1)
        page = self.client.get(response["Location"])
        self.assertContains(page, "Announced. Players can answer now.")
        self.assertContains(page, "Who's coming")

    def test_a_chosen_preset_fills_the_session_and_the_page_shows_it(self):
        response = self.post(chip_preset_id=self.preset().pk)
        night = GameNight.objects.get()
        self.assertEqual(night.chip_values[0]["value"], 2500)
        self.assertContains(self.client.get(response["Location"]), "Edit chip values")

    def test_without_the_options_nothing_is_told_and_no_values_are_set(self):
        self.post(chip_preset_id="")
        night = GameNight.objects.get()
        self.assertEqual((night.chip_values, night.announced_at), ([], None))
        self.assertFalse(Notice.objects.exists())

    def test_a_preset_of_the_other_unit_is_refused_and_the_form_stays(self):
        page = self.post(chip_preset_id=self.preset("Chip set", "chips").pk, location="Kept place", announce="on")
        self.assertContains(page, "uses another unit", status_code=422)
        self.assertContains(page, 'value="Kept place"', status_code=422)
        self.assertFalse(GameNight.objects.exists())
        self.assertFalse(Notice.objects.exists())

    def test_an_archived_preset_is_refused_with_a_reason(self):
        preset = self.preset()
        services.archive_chip_preset(self.host, preset.pk, uuid.uuid4())
        page = self.post(chip_preset_id=preset.pk)
        self.assertContains(page, "no longer available", status_code=422)
        self.assertFalse(GameNight.objects.exists())

    def test_a_bad_start_time_blocks_only_when_announcing(self):
        self.assertFalse(GameNight.objects.exists())
        page = self.post(announce="on", start_time="late")
        self.assertContains(page, "Enter a valid time", status_code=422)
        self.assertFalse(GameNight.objects.exists())
        self.post(start_time="late")
        self.assertIsNone(GameNight.objects.get().start_time)

    def test_a_refused_form_is_a_422_and_an_accepted_one_redirects(self):
        # Turbo draws a refusal over the form only when it is a 422, and follows the redirect.
        self.assertEqual(self.post(announce="on", start_time="late").status_code, 422)
        self.assertRedirects(self.post(), reverse("night", args=[GameNight.objects.get().pk]))

    def test_the_form_leaves_in_the_app_and_goes_deeper(self):
        self.assertContains(self.client.get(self.url), '<form method="post" data-turbo="true" data-go="deeper" class="form-section form-groups"')

    def test_a_double_tap_tells_nobody_twice(self):
        request_id = uuid.uuid4()
        self.post(announce="on", request_id=request_id)
        self.post(announce="on", request_id=request_id)
        self.assertEqual(GameNight.objects.count(), 1)
        self.assertEqual(Notice.objects.count(), 1)


class SessionPageLeadTests(TestCase):
    """Before set 1 opens, one primary action leads the host's first screen."""

    OPEN_SET = 'class="btn{} btn-block" href="{}">Open set 1</a>'

    def setUp(self):
        self.group, self.host = make_group()
        self.client.force_login(self.host.user)

    def lead(self, session):
        return self.OPEN_SET.format("{}", reverse("session", args=[session.pk]))

    def page(self, session):
        return self.client.get(reverse("night", args=[session.night_id])).content.decode()

    def test_a_draft_not_yet_announced_still_leads_with_the_set(self):
        session = make_session(self.host)
        html = self.page(session)
        self.assertIn(self.lead(session).format(" btn-primary"), html)
        self.assertIn('class="btn btn-block">Announce to the group', html)

    def test_after_announcing_open_set_leads_again(self):
        session = make_session(self.host)
        services.announce_night(session.night_id, self.host)
        self.assertIn(self.lead(session).format(" btn-primary"), self.page(session))

    def test_an_open_set_keeps_its_primary_button(self):
        session = make_session(self.host, state="open")
        self.assertIn(self.lead(session).format(" btn-primary"), self.page(session))


class NewSessionRetryTests(TestCase):
    """What a host meets on going back to the form, or after a refusal."""

    def setUp(self):
        self.group, self.host = make_group()
        add_player(self.group, "ben")
        self.table = make_table(self.host)
        self.url = reverse("session_create", args=[self.group.pk])
        self.client.force_login(self.host.user)

    def post(self, **options):
        return self.client.post(self.url, {
            "table_id": self.table.pk, "game_date": "2026-10-09", "game_type": "nlh", "unit": "php", "small_blind": "10",
            "big_blind": "20", "min_buy_in": "500", "max_buy_in": "2000", "default_buy_in": "1000", **options,
        })

    def test_the_form_is_never_restored_with_a_used_request_id(self):
        page = self.client.get(self.url)
        self.assertIn("no-store", page["Cache-Control"])
        self.assertNotEqual(page.context["request_id"], self.client.get(self.url).context["request_id"])

    def test_a_repeat_says_announced_only_when_the_session_is_announced(self):
        request_id = uuid.uuid4()
        self.post(request_id=request_id)
        response = self.post(request_id=request_id, announce="on")
        self.assertIsNone(GameNight.objects.get().announced_at)
        self.assertNotContains(self.client.get(response["Location"]), "Announced. Players can answer now.")

    def test_a_refused_form_keeps_the_stakes_preset_it_was_filled_from(self):
        first = make_preset(self.host, name="A first")
        chosen = make_preset(self.host, name="Z chosen")
        page = self.post(preset_id=chosen.pk, announce="on", start_time="late")
        self.assertContains(page, f'name="preset_id" value="{chosen.pk}"', status_code=422)
        self.assertNotContains(page, f'name="preset_id" value="{first.pk}"', status_code=422)

    def test_the_start_time_has_no_step_that_could_block_the_form_while_hidden(self):
        self.assertNotRegex(self.client.get(self.url).content.decode(), r'name="start_time"[^>]*step=')

    def test_a_chip_preset_field_is_refused_with_one_reason_for_a_bad_or_lost_preset(self):
        for value in ("9999", "not-a-number"):
            self.assertContains(self.post(chip_preset_id=value), "no longer available", status_code=422)
        self.assertFalse(GameNight.objects.exists())
