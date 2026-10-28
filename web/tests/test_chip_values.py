"""Session setup and the actual denomination-count write through signed-in pages."""
import json
import uuid

from django.test import TestCase, override_settings
from django.utils.html import escape
from django.urls import reverse

from games import services as games
from groups.tests.helpers import add_player, make_group
from ledger import services
from ledger.models import CountEntry, FinalCount
from ledger.tests.helpers import Night


class ChipPagesTests(TestCase):
    def setUp(self):
        self.n = Night("A")
        self.player = self.n.add_login_player("ben")
        self.n.buy("A", 1000)
        self.n.buy("ben", 1000)
        self.n.go("reconciliation")
        self.night = self.n.session.night
        self.client.force_login(self.n.host.user)
        self.setup_url = reverse("chip_values", args=[self.night.pk])
        self.count_url = reverse("chip_count", args=[self.n.session.pk, self.n.players["ben"].pk])

    def configure(self):
        games.set_chip_values(self.night.pk, self.n.host, [
            {"colour": "red", "label": "Small", "value": 2500},
            {"colour": "green", "label": "", "value": 10000}], uuid.uuid4(), revision=0)

    def test_host_can_save_values_from_the_setup_form(self):
        response = self.client.post(self.setup_url, {
            "revision": "0", "request_id": uuid.uuid4(), "chips-TOTAL_FORMS": "1", "chips-INITIAL_FORMS": "0",
            "chips-0-colour": "red", "chips-0-label": "Small", "chips-0-value": "25.50",
        }, follow=True)
        self.assertContains(response, "Chip values saved")
        self.assertContains(response, "₱25.50")
        self.night.refresh_from_db()
        self.assertEqual(self.night.chip_values[0]["value"], 2550)

    def test_refused_setup_keeps_the_typed_value(self):
        response = self.client.post(self.setup_url, {
            "revision": "0", "chips-TOTAL_FORMS": "1", "chips-INITIAL_FORMS": "0",
            "chips-0-colour": "red", "chips-0-label": "Small", "chips-0-value": "25.005",
        })
        self.assertContains(response, "25.005")
        self.assertContains(response, "at most two decimal places")

    def test_add_colour_without_javascript_preserves_unsaved_rows(self):
        response = self.client.post(self.setup_url, {
            "intent": "add", "revision": "0", "chips-TOTAL_FORMS": "1", "chips-INITIAL_FORMS": "0",
            "chips-0-colour": "red", "chips-0-label": "Small", "chips-0-value": "25",
        })
        self.assertContains(response, 'name="chips-1-colour"')
        self.assertContains(response, 'value="25"')
        self.night.refresh_from_db()
        self.assertEqual(self.night.chip_values_revision, 0)

    def test_player_submits_quantities_then_host_confirms_and_cash_out_balances(self):
        self.configure()
        self.client.force_login(self.player.user)
        response = self.client.post(self.count_url, {"chip_revision": "1", "qty_red": "4", "qty_green": "9",
                                                  "amount": "1", "request_id": uuid.uuid4()}, follow=True)
        self.assertContains(response, "Count sent to the host")
        entry = CountEntry.objects.get(participant=self.n.players["ben"], is_current=True)
        self.assertEqual(entry.amount, 100000)
        self.client.force_login(self.n.host.user)
        response = self.client.post(reverse("count_confirm", args=[self.n.session.pk]), {
            f"entry_{self.n.players['ben'].pk}": entry.pk, "request_id": uuid.uuid4()}, follow=True)
        self.assertContains(response, "1 count confirmed")
        count = FinalCount.objects.get(participant=self.n.players["ben"], is_current=True)
        self.assertEqual(count.chip_breakdown, entry.chip_breakdown)
        services.confirm_count(self.n.session.pk, self.n.host, self.n.players["A"].pk, 100000, uuid.uuid4())
        counts = FinalCount.objects.filter(session=self.n.session, is_current=True).values_list("pk", flat=True)
        response = self.client.post(reverse("cash_out_counted", args=[self.n.session.pk]), {
            "count_id": list(counts), "request_id": uuid.uuid4()}, follow=True)
        self.assertContains(response, "All counts match buy-ins.")

    def test_host_can_confirm_a_chip_count_directly(self):
        self.configure()
        response = self.client.post(self.count_url, {"chip_revision": "1", "qty_red": "2", "qty_green": "3",
                                                   "request_id": uuid.uuid4()}, follow=True)
        self.assertContains(response, "Count confirmed.")
        self.assertEqual(FinalCount.objects.get(participant=self.n.players["ben"]).amount, 35000)

    def test_stale_and_invalid_counts_keep_quantities_without_recording(self):
        self.configure()
        response = self.client.post(self.count_url, {"chip_revision": "0", "qty_red": "17", "request_id": uuid.uuid4()})
        self.assertContains(response, 'value="17"')
        self.assertFalse(FinalCount.objects.exists())
        response = self.client.post(self.count_url, {"chip_revision": "1", "qty_red": "1.5", "request_id": uuid.uuid4()})
        self.assertContains(response, 'value="1.5"')
        self.assertFalse(FinalCount.objects.exists())

    def test_player_cannot_edit_values_or_count_for_another_player(self):
        self.configure()
        self.client.force_login(self.player.user)
        self.assertEqual(self.client.get(self.setup_url).status_code, 403)
        url = reverse("chip_count", args=[self.n.session.pk, self.n.players["A"].pk])
        self.assertEqual(self.client.post(url, {"chip_revision": "1", "empty_stack": "1"}).status_code, 404)

    def test_outside_group_cannot_open_either_form(self):
        self.configure()
        _, outsider = make_group(host_name="outsider")
        self.client.force_login(outsider.user)
        self.assertEqual(self.client.get(self.setup_url).status_code, 404)
        self.assertEqual(self.client.get(self.count_url).status_code, 404)

    def test_session_and_count_pages_offer_the_saved_values(self):
        self.configure()
        response = self.client.get(reverse("night", args=[self.night.pk]))
        self.assertContains(response, "Small")
        response = self.client.get(reverse("session", args=[self.n.session.pk]))
        self.assertContains(response, "Count by chips")
        self.assertContains(response, 'data-chip-quantity')

    def test_empty_stack_is_explicit_and_locks_values(self):
        self.configure()
        self.client.post(self.count_url, {"chip_revision": "1", "request_id": uuid.uuid4()})
        self.assertFalse(FinalCount.objects.exists())
        self.client.post(self.count_url, {"chip_revision": "1", "empty_stack": "1", "request_id": uuid.uuid4()})
        self.assertEqual(FinalCount.objects.get(participant=self.n.players["ben"]).amount, 0)
        response = self.client.get(self.setup_url)
        self.assertContains(response, "Chip values are locked")


class BatchChipFormTests(TestCase):
    """The count list's hidden chip fields reach "Confirm all counts", and a refusal keeps them."""

    def setUp(self):
        self.n = Night("A")
        self.player = self.n.add_login_player("ben")
        self.n.buy("A", 1000)
        self.n.buy("ben", 1000)
        self.n.go("reconciliation")
        games.set_chip_values(self.n.session.night_id, self.n.host, [
            {"colour": "red", "label": "Small", "value": 2500},
            {"colour": "green", "label": "", "value": 10000}], uuid.uuid4(), revision=0)
        self.a, self.ben = self.n.players["A"].pk, self.n.players["ben"].pk
        self.url = reverse("count_confirm", args=[self.n.session.pk])
        self.client.force_login(self.n.host.user)

    def chips(self, pairs, revision=1, empty_stack=False):
        return json.dumps({"quantities": pairs, "revision": revision, "empty_stack": empty_stack})

    def current(self, pid):
        return FinalCount.objects.filter(participant_id=pid, is_current=True).first()

    def test_typed_and_chip_counts_confirm_together(self):
        response = self.client.post(self.url, {
            f"count_{self.a}": "800", f"count_{self.ben}": "1100", f"chips_{self.ben}": self.chips([["red", "4"], ["green", "10"]]),
            "request_id": uuid.uuid4()}, follow=True)
        self.assertContains(response, "2 counts confirmed")
        self.assertEqual(self.current(self.a).amount, 80000)
        self.assertEqual(self.current(self.ben).amount, 110000)
        self.assertEqual([row["quantity"] for row in self.current(self.ben).chip_breakdown], [4, 10])

    def test_a_chip_count_alone_is_enough(self):
        response = self.client.post(self.url, {f"chips_{self.ben}": self.chips([], empty_stack=True),
                                               "request_id": uuid.uuid4()}, follow=True)
        self.assertContains(response, "1 count confirmed")
        self.assertEqual(self.current(self.ben).amount, 0)

    def test_a_refusal_saves_nothing_and_keeps_typed_counts_and_chips(self):
        raw = self.chips([["red", "4"]])
        response = self.client.post(self.url, {f"count_{self.a}": "800", f"count_{self.ben}": "5", f"chips_{self.ben}": raw,
                                               "request_id": uuid.uuid4()}, follow=True)
        self.assertContains(response, "but the chips add up to ₱100")
        self.assertContains(response, "Nothing was saved")
        self.assertIsNone(self.current(self.a))
        self.assertIsNone(self.current(self.ben))
        self.assertContains(response, f'name="chips_{self.ben}" value="{escape(raw)}"', html=False)
        self.assertContains(response, 'value="800"')

    def test_an_unreadable_chip_field_is_refused_by_name(self):
        for raw in ["{", '{"quantities": "red", "revision": 1}', '{"quantities": [["red", 4]], "revision": 1}',
                    '{"quantities": [], "revision": "1"}', '[]', "x" * 5000]:
            with self.subTest(raw=raw[:40]):
                response = self.client.post(self.url, {f"chips_{self.ben}": raw, "request_id": uuid.uuid4()}, follow=True)
                self.assertContains(response, "ben: the chip count could not be read")
        self.assertIsNone(self.current(self.ben))

    def test_count_rows_carry_an_empty_chip_field(self):
        response = self.client.get(reverse("session", args=[self.n.session.pk]))
        self.assertContains(response, f'name="chips_{self.ben}" value=""', html=False)


@override_settings(PLAYER_ENTRIES=True)
class PlayerChipFormTests(TestCase):
    def setUp(self):
        self.n = Night("A")
        self.player = self.n.add_login_player("ben")
        self.n.buy("A", 1000)
        self.n.buy("ben", 1000)
        self.n.go("reconciliation")
        games.set_chip_values(self.n.session.night_id, self.n.host, [
            {"colour": "red", "label": "Small", "value": 2500}], uuid.uuid4(), revision=0)
        self.url = reverse("count_enter", args=[self.n.session.pk])
        self.client.force_login(self.player.user)

    def test_the_card_sends_chips_with_the_amount(self):
        chips = json.dumps({"quantities": [["red", "8"]], "revision": 1, "empty_stack": False})
        response = self.client.post(self.url, {"amount": "200", "chips": chips, "request_id": uuid.uuid4()}, follow=True)
        self.assertContains(response, "Count sent to the host")
        entry = CountEntry.objects.get(participant=self.n.players["ben"], is_current=True)
        self.assertEqual(entry.amount, 20000)
        self.assertEqual(entry.chip_breakdown[0]["quantity"], 8)

    def test_an_amount_that_differs_from_the_chips_is_refused(self):
        chips = json.dumps({"quantities": [["red", "8"]], "revision": 1, "empty_stack": False})
        response = self.client.post(self.url, {"amount": "150", "chips": chips, "request_id": uuid.uuid4()}, follow=True)
        self.assertContains(response, "but the chips add up to ₱200")
        self.assertFalse(CountEntry.objects.filter(participant=self.n.players["ben"]).exists())
