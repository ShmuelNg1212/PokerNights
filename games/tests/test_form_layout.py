"""The stakes forms are laid out in titled groups with pairs. What they save is tested elsewhere."""

import re
import uuid

from django.test import TestCase
from django.urls import reverse

from games.models import GameNight
from games.tests.helpers import STAKES, make_preset, make_session, make_table
from groups.tests.helpers import make_group

STAKES_NAMES = ["small_blind", "big_blind", "min_buy_in", "max_buy_in", "default_buy_in"]
RAKE_NAMES = ["rake_mode", "rake_mode", "rake_mode", "rake_flat", "rake_percentage"]


def control_names(page):
    """The names of the visible controls of the POST form, in document order."""
    html = page.content.decode()
    form = html[html.index('<form method="post" class="form-section form-groups"'):]
    form = form[:form.index("</form>")]
    return [name for name in re.findall(r'<(?:input|select)[^>]*\bname="([^"]+)"', form)
            if name not in ("csrfmiddlewaretoken", "preset_id", "request_id")]


class FormLayoutTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.table = make_table(self.host, preset=make_preset(self.host))
        self.client.force_login(self.host.user)
        self.new_url = reverse("session_create", args=[self.group.pk])

    def test_new_session_groups_and_order(self):
        page = self.client.get(self.new_url)
        self.assertEqual(control_names(page), ["table_id", "game_date", "location", "game_type", "unit", *STAKES_NAMES, *RAKE_NAMES])
        html = page.content.decode()
        titles = re.findall(r'class="group-title"[^>]*>([^<]+)<', html)
        self.assertEqual(titles, ["When and where", "Game", "Stakes", "Rake per buy-in"])
        self.assertEqual(html.count('class="field-pair'), 3)
        self.assertContains(page, "Type each amount in pesos, or in chips for a chips game.", count=1)

    def test_every_control_keeps_its_label_help_and_ids(self):
        html = self.client.get(self.new_url).content.decode()
        for name in ["table_id", "game_date", "location", "game_type", "unit", *STAKES_NAMES, "rake_flat", "rake_percentage"]:
            self.assertEqual(html.count(f'<label for="id_{name}">'), 1, name)
            self.assertEqual(html.count(f' id="id_{name}"'), 1, name)
        for name in ("unit", "default_buy_in", "rake_flat", "rake_percentage", "rake_mode"):
            self.assertEqual(html.count(f'id="id_{name}_helptext"'), 1, name)
        self.assertIn('aria-describedby="id_unit_helptext"', html)
        self.assertEqual(html.count("<legend"), 1)

    def test_refused_form_keeps_values_and_puts_each_error_under_its_field(self):
        data = {"table_id": self.table.pk, "game_date": "", "location": "Miguel's", "game_type": "nlh", "unit": "php",
                **{name: "" for name in STAKES_NAMES}, "small_blind": "10", "rake_mode": "flat", "rake_flat": ""}
        page = self.client.post(self.new_url, data)
        html = page.content.decode()
        self.assertEqual(GameNight.objects.count(), 0)
        for name in ("game_date", "big_blind", "min_buy_in", "max_buy_in", "default_buy_in", "rake_flat"):
            self.assertEqual(html.count(f' id="id_{name}_error"'), 1, name)
        self.assertNotIn('id="id_small_blind_error"', html)
        self.assertIn('value="Miguel&#x27;s"', html)
        self.assertIn('name="small_blind" value="10"', html)
        self.assertRegex(html, r'value="flat"[^>]*checked')

    def test_new_session_saves_what_it_saved_before(self):
        data = {"table_id": self.table.pk, "game_date": "2026-10-09", "location": "Miguel's place", "game_type": "nlh",
                "unit": "php", **STAKES, "rake_mode": "percent", "rake_percentage": "5"}
        response = self.client.post(self.new_url, data)
        night = GameNight.objects.get()
        session = night.sets.get()
        self.assertRedirects(response, reverse("session", args=[session.pk]))
        settings = session.settings_versions.get()
        self.assertEqual((night.location, night.unit, str(night.game_date)), ("Miguel's place", "php", "2026-10-09"))
        self.assertEqual((settings.rake_mode, settings.rake_basis_points), ("percent", 500))
        self.assertEqual(settings.stakes(), {name: value * 100 for name, value in STAKES.items()})  # typed in pesos

    def test_set_settings_groups_and_locked_fields(self):
        from ledger import services as ledger
        session = make_session(self.host, table=self.table, state="open")
        url = reverse("session_settings", args=[session.pk])
        page = self.client.get(url)
        self.assertEqual(control_names(page), ["unit", *STAKES_NAMES, *RAKE_NAMES])
        titles = re.findall(r'class="group-title"[^>]*>([^<]+)<', page.content.decode())
        self.assertEqual(titles, ["Game", "Stakes", "Rake per buy-in"])
        from games import services as games
        player = games.add_participant(session.pk, self.host, self.host.pk)
        games.transition(session.pk, self.host, "start", opening_buy_ins=False)
        ledger.record_buy_in(session.pk, self.host, player.pk, 100000, uuid.uuid4())
        page = self.client.get(url)
        self.assertContains(page, "Buy-ins are recorded, so the unit cannot change.")
        self.assertContains(page, "Rake is locked")
        self.assertRegex(page.content.decode(), r'<select[^>]*name="unit"[^>]*disabled')

    def test_preset_form_groups(self):
        page = self.client.get(reverse("preset_create", args=[self.group.pk]))
        self.assertEqual(control_names(page), ["name", "game_type", "unit", *STAKES_NAMES])
        titles = re.findall(r'class="group-title"[^>]*>([^<]+)<', page.content.decode())
        self.assertEqual(titles, ["Game", "Stakes"])
        self.assertEqual(page.content.decode().count('class="field-pair'), 3)
