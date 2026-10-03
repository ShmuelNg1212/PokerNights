"""A game counts in pesos or in chips. A chips game has no peso value anywhere."""

import datetime
import uuid

from django.test import TestCase
from django.urls import reverse

from games import services as games
from games.models import GameSession, SettingsPreset
from games.tests.helpers import CHIP_STAKES, STAKES, make_table
from groups.errors import RuleError
from groups.tests.helpers import make_group
from ledger import queries as ledger_queries
from ledger import services as ledger
from ledger.models import PlayerResult
from ledger.tests.helpers import Night
from settlement import queries, services as settlement
from settlement.models import Transfer


def chips_night(state="reconciliation"):
    """The worked example as a chips game: A 1,000 → 1,600, B 1,000 → 700, C 500 → 200 chips."""
    night = Night("A", "B", "C", unit="chips")
    night.buy("A", 1000)
    night.buy("B", 1000)
    night.buy("C", 500)
    if state == "reconciliation":
        night.go("reconciliation")
        for name, chips in zip("ABC", (1600, 700, 200)):
            night.cash(name, chips)
    return night


class ChipsGameTests(TestCase):
    def test_amounts_are_stored_as_whole_chips(self):
        night = chips_night()
        self.assertEqual(night.session.unit, "chips")
        summary = ledger_queries.summary(night.session)
        self.assertEqual((summary.total, summary.cashed_out, summary.in_play), (2500, 2500, 0))

    def test_finalizes_and_settles_in_chips(self):
        night = chips_night()
        settlement.finalize(night.session.pk, night.host)
        outcome = queries.outcome(night.session)
        self.assertEqual([(r.net, r.unit) for r in outcome.results], [(600, "chips"), (-300, "chips"), (-300, "chips")])
        self.assertEqual(outcome.finalization.unit, "chips")
        settlement.close_night(night.session.night_id, night.host)
        transfers = queries.night_outcome(night.session.night).transfers
        self.assertEqual(
            [(t.payer.display_name, t.payee.display_name, t.amount) for t in transfers], [("B", "A", 300), ("C", "A", 300)]
        )

    def test_balance_check_and_override_work_in_chips(self):
        night = chips_night()
        ledger.reverse_cash_out(night.session.pk, night.host, night.session.cash_outs.get(participant=night.players["C"]).pk, "recount")
        night.cash("C", 250)
        balance = ledger_queries.balance(night.session)
        self.assertEqual((balance.difference, balance.difference_text), (50, "50 chips"))
        self.assertIn("50 chips too much", balance.explanation)
        ledger.record_override(night.session.pk, night.host, "miscount", "equal", None, uuid.uuid4())
        self.assertEqual([line.adjustment for line in ledger_queries.summary(night.session).lines], [-17, -17, -16])
        settlement.finalize(night.session.pk, night.host)
        self.assertEqual(sum(PlayerResult.objects.values_list("net", flat=True)), 0)

    def test_buy_in_limits_are_in_chips(self):
        night = Night("A", unit="chips")
        with self.assertRaisesMessage(RuleError, "between 500 chips and 2,000 chips"):
            night.buy("A", 100)

    def test_no_peso_sign_on_any_screen_of_a_chips_game(self):
        night = chips_night()
        ledger.reverse_cash_out(night.session.pk, night.host, night.session.cash_outs.last().pk, "recount")
        night.cash("C", 150)
        ledger.record_override(night.session.pk, night.host, "short", "player", night.players["A"].pk, uuid.uuid4())
        self.client.force_login(night.host.user)
        counting = self.client.get(reverse("session", args=[night.session.pk]))
        settlement.finalize(night.session.pk, night.host)
        settlement.close_night(night.session.night_id, night.host)
        settlement.mark_paid(night.session.night_id, night.host, Transfer.objects.first().pk, uuid.uuid4())
        pages = [
            counting,
            self.client.get(reverse("session", args=[night.session.pk])),
            self.client.get(reverse("session_log", args=[night.session.pk])),
            self.client.get(reverse("session_state", args=[night.session.pk])),
            self.client.get(reverse("night", args=[night.session.night_id])),
        ]
        for page in pages:
            self.assertNotContains(page, "₱")
        self.assertContains(pages[1], "Chips game")
        self.assertContains(pages[1], "+650 chips")
        self.assertContains(pages[4], "<strong>B</strong> pays <strong>A</strong>")
        self.assertContains(pages[4], "300 chips")
        self.assertContains(pages[2], "Finalized set 1: 2,500 chips bought in")

    def test_chip_input_must_be_whole(self):
        night = chips_night(state="running")
        self.client.force_login(night.host.user)
        url = reverse("cash_out_add", args=[night.session.pk])
        page = self.client.post(url, {"participant_id": night.players["A"].pk, "amount": "1600.50"}, follow=True)
        self.assertContains(page, "Enter a whole number of chips")
        self.assertEqual(night.session.cash_outs.count(), 0)
        page = self.client.post(url, {"participant_id": night.players["A"].pk, "amount": "1,600"}, follow=True)
        self.assertContains(page, "Cashed out 1,600 chips")
        page = self.client.post(reverse("buy_in_add", args=[night.session.pk]), {"participant_id": night.players["A"].pk, "amount": "₱1000"}, follow=True)
        self.assertContains(page, "Enter a whole number of chips")


class PesosGameShowsNoChipsTests(TestCase):
    def test_pesos_game_never_mentions_chips(self):
        night = Night("A", "B")
        night.buy("A", 1000)
        night.buy("B", 1000)
        night.go("reconciliation")
        night.cash("A", 1500)
        night.cash("B", 500)
        self.client.force_login(night.host.user)
        counting = self.client.get(reverse("session", args=[night.session.pk]))
        settlement.finalize(night.session.pk, night.host)
        for page in (counting, self.client.get(reverse("session", args=[night.session.pk])), self.client.get(reverse("session_log", args=[night.session.pk]))):
            self.assertNotContains(page, "chips")
            self.assertNotContains(page, "Chips")
        self.assertEqual(PlayerResult.objects.values_list("unit", flat=True).distinct().get(), "php")


class UnitChoiceTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.table = make_table(self.host)
        self.client.force_login(self.host.user)

    def test_forms_offer_pesos_by_default_and_no_chips_per_buy_in(self):
        for name in ("preset_create", "session_create"):
            page = self.client.get(reverse(name, args=[self.group.pk]))
            self.assertContains(page, '<option value="php" selected>Pesos (₱)</option>', html=True)
            self.assertContains(page, '<option value="chips">Chips</option>', html=True)
            self.assertNotContains(page, "chips_per_buy_in")
            self.assertNotContains(page, "Chips for the usual buy-in")

    def test_chips_preset_is_typed_in_chips_and_fills_a_new_game(self):
        self.client.post(reverse("preset_create", args=[self.group.pk]), {
            "name": "Play chips", "game_type": "nlh", "unit": "chips", "small_blind": "10", "big_blind": "20",
            "min_buy_in": "500", "max_buy_in": "2,000", "default_buy_in": "1000",
        })
        preset = SettingsPreset.objects.get()
        self.assertEqual((preset.unit, preset.max_buy_in, preset.small_blind), ("chips", 2000, 10))
        group_page = self.client.get(reverse("group", args=[self.group.pk]))
        self.assertContains(group_page, "buy-in 500 chips–2,000 chips")
        form_page = self.client.get(reverse("session_create", args=[self.group.pk]), {"preset": preset.pk})
        self.assertContains(form_page, '<option value="chips" selected>Chips</option>', html=True)
        self.assertContains(form_page, 'value="2000"')

    def test_chips_form_refuses_decimals(self):
        page = self.client.post(reverse("preset_create", args=[self.group.pk]), {
            "name": "Bad", "game_type": "nlh", "unit": "chips", "small_blind": "0.50", "big_blind": "1",
            "min_buy_in": "500", "max_buy_in": "2000", "default_buy_in": "1000",
        })
        self.assertContains(page, "Enter a whole number of chips")
        self.assertEqual(SettingsPreset.objects.count(), 0)

    def test_new_game_takes_the_chosen_unit(self):
        self.client.post(reverse("session_create", args=[self.group.pk]), {
            "table_id": self.table.pk, "game_date": "2026-10-09", "game_type": "nlh", "unit": "chips",
            "small_blind": "10", "big_blind": "20", "min_buy_in": "500", "max_buy_in": "2000", "default_buy_in": "1000",
        })
        session = GameSession.objects.get()
        self.assertEqual((session.unit, games.current_settings(session).default_buy_in), ("chips", 1000))

    def test_unknown_unit_is_refused(self):
        with self.assertRaises(RuleError):
            games.create_session(self.host, {
                "table_id": self.table.pk, "game_date": datetime.date(2026, 10, 9), "game_type": "nlh",
                "unit": "dollars", **STAKES,
            })


class UnitChangeTests(TestCase):
    def test_unit_can_change_before_the_first_buy_in(self):
        night = Night("A", state="open")
        games.update_settings(night.session.pk, night.host, {**CHIP_STAKES, "unit": "chips"})
        session = night.refresh()
        self.assertEqual((session.unit, games.current_settings(session).default_buy_in), ("chips", 1000))

    def test_unit_cannot_change_once_a_buy_in_is_accepted(self):
        night = Night("A", state="open")
        buy_in = night.buy("A", 1000)
        with self.assertRaisesMessage(RuleError, "unit cannot change"):
            games.update_settings(night.session.pk, night.host, {**CHIP_STAKES, "unit": "chips"})
        self.assertEqual(night.refresh().unit, "php")
        ledger.reverse_buy_in(night.session.pk, night.host, buy_in.pk, "wrong unit")
        games.update_settings(night.session.pk, night.host, {**CHIP_STAKES, "unit": "chips"})
        self.assertEqual(night.refresh().unit, "chips")

    def test_settings_page_locks_the_unit_field_when_money_is_in(self):
        night = Night("A", state="open")
        self.client.force_login(night.host.user)
        url = reverse("session_settings", args=[night.session.pk])
        self.assertNotContains(self.client.get(url), "the unit cannot change")
        night.buy("A", 1000)
        self.assertContains(self.client.get(url), "the unit cannot change")
        # A hand-made request that tries to switch the unit is ignored: the field is disabled.
        self.client.post(url, {"unit": "chips", "small_blind": "10", "big_blind": "20", "min_buy_in": "500", "max_buy_in": "2000", "default_buy_in": "1000"})
        self.assertEqual(night.refresh().unit, "php")

    def test_blinds_can_still_change_after_buy_ins(self):
        night = Night("A")
        night.buy("A", 1000)
        games.update_settings(night.session.pk, night.host, {**STAKES, "small_blind": 2000, "big_blind": 4000})
        self.assertEqual(games.current_settings(night.session).big_blind, 4000)
