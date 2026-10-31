"""Where New session starts from, and a first-table form sent again after a table exists."""
import datetime
import json
import re
import uuid

from django.test import TestCase
from django.urls import reverse

from games import services
from games.models import GameNight, Table
from games.tests.helpers import make_preset, make_session, make_table
from groups.errors import RuleError
from groups.tests.helpers import make_group


class StartsFromTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.client.force_login(self.host.user)
        self.url = reverse("session_create", args=[self.group.pk])

    def page(self, query=""):
        return self.client.get(self.url + query).content.decode()

    def value(self, html, name):
        return re.search(rf'name="{name}" value="([^"]*)"', html).group(1)

    def last_session(self, **overrides):
        table = make_table(self.host, name="Garage")
        return make_session(self.host, table=table, small_blind=5000, big_blind=10000, min_buy_in=100000, max_buy_in=500000, default_buy_in=200000, location="Carlo place", **overrides)

    def test_a_preset_nobody_chose_does_not_replace_last_weeks_stakes(self):
        make_preset(self.host, name="Small")
        self.last_session()
        html = self.page()
        self.assertEqual(self.value(html, "small_blind"), "50")
        self.assertEqual(self.value(html, "default_buy_in"), "2000")
        self.assertIn("₱50 / ₱100", html)
        self.assertNotIn('name="preset_id"', html)

    def test_the_chooser_says_it_starts_from_last_session_and_can_go_back(self):
        make_preset(self.host, name="Small")
        self.last_session()
        html = self.page()
        option = re.search(r'<option value="" data-fill="([^"]*)" selected>Same as last session</option>', html)
        self.assertIsNotNone(option)
        self.assertEqual(json.loads(option.group(1).replace("&quot;", '"'))["small_blind"], "50")

    def test_a_chosen_preset_wins(self):
        preset = make_preset(self.host, name="Small")
        self.last_session()
        html = self.page(f"?preset={preset.pk}")
        self.assertEqual(self.value(html, "small_blind"), "10")
        self.assertIn(f'name="preset_id" value="{preset.pk}"', html)

    def test_the_last_tables_own_preset_wins(self):
        preset = make_preset(self.host, name="Garage game")
        table = make_table(self.host, name="Garage", preset=preset)
        make_session(self.host, table=table, small_blind=5000, big_blind=10000, min_buy_in=100000, max_buy_in=500000, default_buy_in=200000)
        self.assertEqual(self.value(self.page(), "small_blind"), "10")

    def test_another_tables_preset_does_not_apply(self):
        make_table(self.host, name="Rooftop", preset=make_preset(self.host, name="Rooftop game"))
        self.last_session()
        self.assertEqual(self.value(self.page(), "small_blind"), "50")

    def test_the_first_session_of_a_group_with_a_preset_starts_from_it(self):
        make_table(self.host)
        make_preset(self.host, name="Small")
        self.assertEqual(self.value(self.page(), "small_blind"), "10")

    def test_table_and_place_come_from_last_session(self):
        session = self.last_session()
        html = self.page()
        self.assertIn(f'<option value="{session.table_id}" selected>', html)
        self.assertEqual(self.value(html, "location"), "Carlo place")

    def test_an_archived_last_session_is_not_used(self):
        session = self.last_session()
        services.transition(session.pk, self.host, "cancel")
        services.archive_night(session.night_id, self.host)
        self.assertNotRegex(self.page(), r'name="small_blind" value="')

    def test_rake_starts_off_even_when_last_session_had_it(self):
        session = self.last_session()
        services.update_settings(session.pk, self.host, {**services.current_settings(session).stakes(), "rake_mode": "percent", "rake_basis_points": 500}, request_id=uuid.uuid4())
        self.assertRegex(self.page(), r'value="off"[^>]*checked')

    def test_stakes_fold_only_when_known(self):
        make_table(self.host)
        self.assertRegex(self.page(), r'data-stakes-fold open>')
        GameNight.objects.all().delete()
        self.last_session()
        self.assertRegex(self.page(), r'data-stakes-fold>')

    def test_a_refusal_opens_the_stakes_and_keeps_no_preset_it_did_not_have(self):
        make_preset(self.host, name="Small")
        session = self.last_session()
        response = self.client.post(self.url, {
            "request_id": str(uuid.uuid4()), "table_id": session.table_id, "game_date": "2026-10-09", "game_type": "nlh", "unit": "php",
            "small_blind": "50", "big_blind": "", "min_buy_in": "1000", "max_buy_in": "5000", "default_buy_in": "2000", "rake_mode": "off",
        })
        html = response.content.decode()
        self.assertEqual(response.status_code, 422)
        self.assertRegex(html, r'data-stakes-fold open>')
        self.assertNotIn('name="preset_id"', html)
        self.assertIn(">Same as last session</option>", html)


class FirstTableRetryTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.client.force_login(self.host.user)
        self.url = reverse("session_create", args=[self.group.pk])

    def form(self, request_id, name="Rosa's kitchen"):
        return {"request_id": str(request_id), "table_name": name, "table_seats": "9", "game_date": "2026-10-09", "game_type": "nlh", "unit": "php",
                "small_blind": "10", "big_blind": "20", "min_buy_in": "500", "max_buy_in": "5000", "default_buy_in": "1000", "rake_mode": "off"}

    def test_sending_the_same_form_again_changes_nothing(self):
        request_id = uuid.uuid4()
        first = self.client.post(self.url, self.form(request_id))
        second = self.client.post(self.url, self.form(request_id))
        self.assertEqual((first.status_code, second.status_code), (302, 302))
        self.assertEqual(first["Location"], second["Location"])
        self.assertEqual(Table.objects.filter(group=self.group).count(), 1)
        self.assertEqual(GameNight.objects.filter(group=self.group).count(), 1)

    def test_a_second_host_with_the_same_name_shares_the_table(self):
        self.client.post(self.url, self.form(uuid.uuid4()))
        response = self.client.post(self.url, self.form(uuid.uuid4()))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Table.objects.filter(group=self.group).count(), 1)
        self.assertEqual(GameNight.objects.filter(group=self.group).count(), 2)


class ArchivedNameTests(TestCase):
    def test_the_refusal_says_the_name_belongs_to_an_archived_table(self):
        group, host = make_group()
        Table.objects.filter(pk=make_table(host, name="Home").pk).update(archived_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC))
        with self.assertRaisesRegex(RuleError, "archived"):
            services.create_session(host, {"table_name": "Home", "game_date": datetime.date(2026, 10, 9), "game_type": "nlh", "unit": "php",
                                           "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 200000, "default_buy_in": 100000})
