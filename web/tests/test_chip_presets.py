"""Group chip presets through signed-in pages: managing them, and filling a session's chip values from one."""
import uuid

from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from games import services as games
from games.models import ChipPreset
from games.tests.helpers import make_session
from groups.tests.helpers import add_player, make_group
from ledger.tests.helpers import Night

RED = [{"colour": "red", "label": "Small", "value": 2500}, {"colour": "green", "label": "", "value": 10000}]


def rows(*values, **extra):
    """A posted chip values formset: (colour, label, value) per row."""
    data = {"chips-TOTAL_FORMS": str(len(values)), "chips-INITIAL_FORMS": "0", **extra}
    for i, (colour, label, value) in enumerate(values):
        data.update({f"chips-{i}-colour": colour, f"chips-{i}-label": label, f"chips-{i}-value": value})
    return data


class FillFromPresetTests(TestCase):
    def setUp(self):
        self.n = Night("A", state="open")
        self.night = self.n.session.night
        self.host = self.n.host
        self.preset = games.save_chip_preset(self.host, {"name": "Home set", "unit": "php", "values": RED}, uuid.uuid4())
        self.client.force_login(self.host.user)
        self.url = reverse("chip_values", args=[self.night.pk])

    def fill(self, preset_id, **extra):
        return self.client.post(self.url, rows(("", "", ""), intent="preset", preset=str(preset_id), **{"revision": "0", **extra}))

    def test_the_page_offers_presets_of_the_session_unit_only(self):
        games.save_chip_preset(self.host, {"name": "Chip set", "unit": "chips", "values": RED}, uuid.uuid4())
        page = self.client.get(self.url)
        self.assertContains(page, "Start from a preset")
        self.assertContains(page, "Home set")
        self.assertNotContains(page, "Chip set")

    def test_fill_puts_the_preset_in_the_form_and_saves_nothing(self):
        page = self.fill(self.preset.pk)
        self.assertContains(page, "Filled from Home set")
        self.assertContains(page, 'value="25"')
        self.assertContains(page, 'value="100"')
        self.assertContains(page, 'name="from_preset" value="%d"' % self.preset.pk)
        self.night.refresh_from_db()
        self.assertEqual((self.night.chip_values, self.night.chip_values_revision), ([], 0))

    def test_saving_a_filled_form_copies_the_values_and_names_the_preset(self):
        response = self.client.post(self.url, rows(("red", "Small", "25"), ("green", "", "100"),
                                                   revision="0", request_id=uuid.uuid4(), from_preset=str(self.preset.pk)))
        self.assertEqual(response.status_code, 302)
        self.night.refresh_from_db()
        self.assertEqual([r["value"] for r in self.night.chip_values], [2500, 10000])
        self.assertEqual(AuditEvent.objects.get(action="night.chip_values").data["preset"], "Home set")
        games.save_chip_preset(self.host, {"name": "Home set", "unit": "php", "values": [{"colour": "red", "value": 1}]},
                               uuid.uuid4(), preset_id=self.preset.pk)
        self.night.refresh_from_db()
        self.assertEqual(self.night.chip_values[0]["value"], 2500)

    def test_an_edited_fill_is_not_recorded_as_the_preset(self):
        self.client.post(self.url, rows(("red", "Small", "50"), ("green", "", "100"),
                                        revision="0", request_id=uuid.uuid4(), from_preset=str(self.preset.pk)))
        self.assertNotIn("preset", AuditEvent.objects.get(action="night.chip_values").data)

    def test_save_as_preset_with_a_bad_row_says_so_beside_the_button(self):
        page = self.client.post(self.url, rows(("blue", "", ""), intent="save_preset", preset_name="Blues", revision="0"))
        self.assertContains(page, "Check the chip values above, then save them as a preset.")
        self.assertContains(page, '<details class="chip-save-preset" open>')

    def test_wrong_unit_other_group_and_archived_presets_are_refused(self):
        chips = games.save_chip_preset(self.host, {"name": "Chip set", "unit": "chips", "values": RED}, uuid.uuid4())
        _, other_host = make_group("olga", "Other")
        theirs = games.save_chip_preset(other_host, {"name": "Theirs", "unit": "php", "values": RED}, uuid.uuid4())
        gone = games.save_chip_preset(self.host, {"name": "Old", "unit": "php", "values": RED}, uuid.uuid4())
        games.archive_chip_preset(self.host, gone.pk, uuid.uuid4())
        for preset in (chips, theirs, gone):
            with self.subTest(preset=preset.name):
                page = self.fill(preset.pk)
                self.assertContains(page, "Choose a preset from this group")
                self.assertNotContains(page, "Filled from")
        self.night.refresh_from_db()
        self.assertEqual(self.night.chip_values_revision, 0)

    def test_a_locked_session_cannot_be_filled(self):
        games.set_chip_values(self.night.pk, self.host, [{"colour": "blue", "value": 500}], uuid.uuid4(), revision=0)
        self.night.chip_values_locked_at = self.night.created_at
        self.night.save(update_fields=["chip_values_locked_at"])
        page = self.fill(self.preset.pk, revision="1")
        self.assertNotContains(page, "Filled from")
        self.assertNotContains(page, "Start from a preset")
        self.assertContains(page, "Chip values are locked, so a preset cannot fill them.")
        self.night.refresh_from_db()
        self.assertEqual(self.night.chip_values[0]["colour"], "blue")

    def test_save_as_preset_keeps_the_form_and_changes_no_session(self):
        posted = uuid.uuid4()
        page = self.client.post(self.url, rows(("blue", "", "5"), intent="save_preset", preset_name="Blues",
                                               revision="0", request_id=posted))
        self.assertContains(page, "Saved Blues as a group preset")
        self.assertEqual(ChipPreset.objects.get(name="Blues").values[0]["value"], 500)
        self.assertNotContains(page, str(posted))  # the next save is a new request
        self.assertContains(page, 'value="5"')
        self.night.refresh_from_db()
        self.assertEqual(self.night.chip_values_revision, 0)

    def test_save_as_preset_on_a_locked_session_uses_the_saved_values(self):
        games.set_chip_values(self.night.pk, self.host, [{"colour": "blue", "value": 500}], uuid.uuid4(), revision=0)
        self.night.chip_values_locked_at = self.night.created_at
        self.night.save(update_fields=["chip_values_locked_at"])
        self.client.post(self.url, {"intent": "save_preset", "preset_name": "Last night", "request_id": uuid.uuid4(),
                                    "chips-TOTAL_FORMS": "1", "chips-INITIAL_FORMS": "1"})
        self.assertEqual(ChipPreset.objects.get(name="Last night").values[0]["colour"], "blue")
        page = self.client.post(self.url, {"intent": "save_preset", "preset_name": "", "request_id": uuid.uuid4(),
                                           "chips-TOTAL_FORMS": "1", "chips-INITIAL_FORMS": "1"})
        self.assertContains(page, '<option value="blue" selected>')  # the saved rows, not blank ones
        self.assertContains(page, 'value="5"')

    def test_save_as_preset_needs_a_name(self):
        page = self.client.post(self.url, rows(("blue", "", "5"), intent="save_preset", preset_name="", revision="0"))
        self.assertContains(page, "Preset name is required")
        self.assertFalse(ChipPreset.objects.filter(values__0__colour="blue").exists())


class PresetPagesTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.client.force_login(self.host.user)
        self.new_url = reverse("chip_preset_create", args=[self.group.pk])
        self.settings_url = reverse("group", args=[self.group.pk]) + "?view=settings"

    def test_host_creates_a_chips_preset_and_sees_it_in_group_settings(self):
        response = self.client.post(self.new_url, rows(("red", "", "25"), ("black", "Big", "100"),
                                                       name="Tournament", unit="chips", request_id=uuid.uuid4()))
        self.assertEqual(response.status_code, 302)
        preset = ChipPreset.objects.get()
        self.assertEqual((preset.unit, [r["value"] for r in preset.values]), ("chips", [25, 100]))
        page = self.client.get(self.settings_url)
        self.assertContains(page, "Chip presets")
        self.assertContains(page, "Tournament")
        self.assertContains(page, reverse("chip_preset_edit", args=[self.group.pk, preset.pk]))

    def test_pesos_values_take_centavos_and_errors_keep_the_typed_rows(self):
        self.client.post(self.new_url, rows(("red", "", "25.50"), name="Home", unit="php", request_id=uuid.uuid4()))
        self.assertEqual(ChipPreset.objects.get().values[0]["value"], 2550)
        page = self.client.post(self.new_url, rows(("red", "", "25.505"), name="Other", unit="php", request_id=uuid.uuid4()))
        self.assertContains(page, "25.505")
        self.assertEqual(ChipPreset.objects.count(), 1)

    def test_edit_and_archive(self):
        preset = games.save_chip_preset(self.host, {"name": "Home", "unit": "php", "values": RED}, uuid.uuid4())
        url = reverse("chip_preset_edit", args=[self.group.pk, preset.pk])
        page = self.client.get(url)
        self.assertContains(page, 'value="Home"')
        self.assertContains(page, 'value="25"')
        self.client.post(url, rows(("red", "", "30"), name="Home", unit="php", request_id=uuid.uuid4()))
        preset.refresh_from_db()
        self.assertEqual(preset.values[0]["value"], 3000)
        self.client.post(url, {"intent": "archive", "request_id": uuid.uuid4()})
        preset.refresh_from_db()
        self.assertIsNotNone(preset.archived_at)
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_players_read_presets_but_cannot_open_the_pages(self):
        preset = games.save_chip_preset(self.host, {"name": "Home", "unit": "php", "values": RED}, uuid.uuid4())
        player = add_player(self.group, "ben")
        self.client.force_login(player.user)
        page = self.client.get(self.settings_url)
        self.assertContains(page, "Home")
        self.assertNotContains(page, reverse("chip_preset_edit", args=[self.group.pk, preset.pk]))
        for url in (self.new_url, reverse("chip_preset_edit", args=[self.group.pk, preset.pk])):
            self.assertIn(self.client.get(url).status_code, (403, 404))
            self.assertIn(self.client.post(url, rows(("red", "", "1"), name="X", unit="php")).status_code, (403, 404))
        self.assertEqual(ChipPreset.objects.count(), 1)

    def test_another_groups_preset_is_not_found(self):
        _, other_host = make_group("olga", "Other")
        theirs = games.save_chip_preset(other_host, {"name": "Theirs", "unit": "php", "values": RED}, uuid.uuid4())
        self.assertEqual(self.client.get(reverse("chip_preset_edit", args=[self.group.pk, theirs.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("chip_preset_edit", args=[theirs.group_id, theirs.pk])).status_code, 404)

    def test_value_fields_use_the_number_keys_by_the_unit_choice(self):
        page = self.client.get(self.new_url).content.decode()
        self.assertIn('data-numpad="amount"', page)
        self.assertIn('name="unit"', page)
