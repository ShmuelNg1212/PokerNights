"""The in-app numpad: what the server gives the script, and what stays when the script is absent."""
import re

from django.test import TestCase, override_settings
from django.urls import reverse

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
