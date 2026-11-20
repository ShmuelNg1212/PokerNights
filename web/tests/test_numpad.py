"""The in-app numpad: what the server gives the script, and what stays when the script is absent."""
import re
import uuid

from django.test import TestCase, override_settings
from django.urls import reverse

from games import services as games
from ledger.tests.helpers import Night


def field(page, name_or_keep):
    """The first input tag whose markup mentions ``name_or_keep``."""
    found = re.search(r"<input[^>]*" + re.escape(name_or_keep) + r"[^>]*>", page.content.decode())
    return found.group(0) if found else ""


class NumpadSwitchTests(TestCase):
    def setUp(self):
        self.night = Night("Ben", "Bea")
        self.client.force_login(self.night.host.user)
        self.url = reverse("session", args=[self.night.session.pk])

    def test_pages_load_the_script_and_turn_it_on(self):
        page = self.client.get(self.url)
        self.assertContains(page, "js/numpad.js")
        self.assertContains(page, 'data-numpad="on"')

    @override_settings(NUMPAD=False)
    def test_the_switch_turns_it_off_without_removing_the_fields(self):
        page = self.client.get(self.url)
        self.assertNotContains(page, 'data-numpad="on"')
        self.assertIn('inputmode="decimal"', field(page, 'data-keep="buy-in-'))


class SheetAmountTests(TestCase):
    def test_pesos_amounts_are_marked_and_keep_the_native_keyboard_until_the_script_runs(self):
        night = Night("Ben", "Bea")
        night.buy("Ben", 1000)
        self.client.force_login(night.host.user)
        page = self.client.get(reverse("session", args=[night.session.pk]))
        for keep in ('data-keep="buy-in-', 'data-keep="cash-out-'):
            tag = field(page, keep)
            self.assertIn('data-numpad="pesos"', tag)
            # The script, not the server, switches the phone's keyboard off.
            self.assertIn('inputmode="decimal"', tag)
            self.assertIn('name="amount"', tag)
        self.assertContains(page, "data-numpad-slot")

    def test_chips_amounts_take_no_decimal_point(self):
        night = Night("Ben", "Bea", unit="chips")
        night.buy("Ben", 1000)
        self.client.force_login(night.host.user)
        page = self.client.get(reverse("session", args=[night.session.pk]))
        self.assertIn('data-numpad="chips"', field(page, 'data-keep="buy-in-'))
        self.assertIn('data-numpad="chips"', field(page, 'data-keep="cash-out-'))
        self.assertNotContains(page, 'data-numpad="pesos"')

    def test_the_buy_in_sheet_has_one_help_line(self):
        night = Night("Ben")
        self.client.force_login(night.host.user)
        page = self.client.get(reverse("session", args=[night.session.pk])).content.decode()
        form = page[page.index('class="stack buy-form"'):]
        form = form[:form.index("</form>")]
        self.assertEqual(form.count('class="hint"'), 1)
        self.assertIn("Allowed: ₱500–₱2,000", form)
        self.assertIn("Rake is Off.", form)


class SetupFormTests(TestCase):
    """Stakes, rake and seats are marked for the numpad and keep working without it."""

    def setUp(self):
        self.night = Night("Ben", state="open")
        self.client.force_login(self.night.host.user)

    def test_stakes_follow_the_unit_and_rake_percentage_takes_a_decimal(self):
        page = self.client.get(reverse("session_settings", args=[self.night.session.pk]))
        for name in ("small_blind", "big_blind", "min_buy_in", "max_buy_in", "default_buy_in", "rake_flat"):
            tag = field(page, f'name="{name}"')
            self.assertIn('data-numpad="amount"', tag, name)
            self.assertIn('inputmode="decimal"', tag, name)
        self.assertIn('data-numpad="percent"', field(page, 'name="rake_percentage"'))
        self.assertContains(page, 'name="unit"')

    def test_new_session_and_preset_forms_are_marked(self):
        group = self.night.group.pk
        for url in (reverse("session_create", args=[group]), reverse("preset_create", args=[group])):
            page = self.client.get(url)
            self.assertIn('data-numpad="amount"', field(page, 'name="small_blind"'), url)

    def test_seats_take_whole_numbers(self):
        page = self.client.get(reverse("group", args=[self.night.group.pk]) + "?view=settings")
        tag = field(page, 'name="seat_count"')
        self.assertIn('data-numpad="whole"', tag)
        self.assertIn('type="number"', tag)


class ChipFieldTests(TestCase):
    """Chip values and chip quantities use the app's keys. The phone keyboard stays until the script runs."""

    def page(self, unit="php"):
        night = Night("Ben", "Bea", unit=unit)
        night.buy("Ben", 1000)
        night.go("reconciliation")
        games.set_chip_values(night.session.night_id, night.host, [
            {"colour": "red", "label": "", "value": 2500}], uuid.uuid4(), revision=0)
        self.client.force_login(night.host.user)
        return night

    def test_setup_values_follow_the_session_unit(self):
        for unit, kind in (("php", "pesos"), ("chips", "chips")):
            night = self.page(unit)
            page = self.client.get(reverse("chip_values", args=[night.session.night_id]))
            tag = field(page, 'name="chips-0-value"')
            self.assertIn(f'data-numpad="{kind}"', tag, unit)
            self.assertIn("inputmode=", tag, unit)

    def test_quantities_take_whole_counts_and_the_form_holds_the_keys(self):
        night = self.page()
        page = self.client.get(reverse("chip_count", args=[night.session.pk, night.players["Ben"].pk]))
        tag = field(page, "data-chip-quantity")
        self.assertIn('data-numpad="count"', tag)
        self.assertIn('inputmode="numeric"', tag)
        form = re.search(r"<form[^>]*data-chip-count.*?</form>", page.content.decode(), re.S).group(0)
        self.assertIn("data-numpad-slot", form)


class AmountFormatTests(TestCase):
    """Amount fields carry their unit marks, and an amount typed with commas is the same amount."""

    def setUp(self):
        self.night = Night("Ben", state="open")
        self.client.force_login(self.night.host.user)

    def test_stakes_fields_carry_both_unit_marks_for_the_stylesheet_to_choose(self):
        page = self.client.get(reverse("session_settings", args=[self.night.session.pk]))
        html = page.content.decode()
        for name in ("small_blind", "default_buy_in", "rake_flat"):
            self.assertRegex(html, r'<span class="unit-field"><span class="unit-pre" aria-hidden="true">₱</span><input[^>]*name="' + name
                             + r'"[^>]*>\s*<span class="unit-post" aria-hidden="true">chips</span></span>', name)

    def test_new_session_shows_the_date_in_words(self):
        import datetime
        page = self.client.get(reverse("session_create", args=[self.night.group.pk]))
        from django.utils import timezone
        today = timezone.localdate()
        self.assertContains(page, f'<p class="hint date-words" data-date-words>{today:%a}, {today:%b} {today.day}</p>')
        self.assertIsInstance(today, datetime.date)

    def test_stakes_typed_with_commas_save_the_same_amounts(self):
        from games.services import current_settings
        url = reverse("session_settings", args=[self.night.session.pk])
        data = {"request_id": uuid.uuid4(), "unit": "php", "small_blind": "1,000", "big_blind": "2,000", "min_buy_in": "10,000",
                "max_buy_in": "1,000,000", "default_buy_in": "20,000.50", "rake_mode": "off", "rake_percentage": "", "rake_flat": ""}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302, response.content.decode()[-3000:] if response.status_code != 302 else "")
        stakes = current_settings(self.night.session).stakes()
        self.assertEqual(stakes, {"small_blind": 100000, "big_blind": 200000, "min_buy_in": 1000000,
                                  "max_buy_in": 100000000, "default_buy_in": 2000050})
