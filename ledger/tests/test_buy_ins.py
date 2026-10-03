import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from games import services as games
from games.tests.helpers import STAKES, make_preset
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import make_user
from ledger import queries, services
from ledger.models import BuyIn, BuyInReversal

from .helpers import Night


class BuyInTests(TestCase):
    def test_buy_in_stores_its_amount_and_the_settings_in_force(self):
        night = Night("A")
        buy_in = night.buy("A", 1000)
        self.assertEqual(buy_in.amount, 100000)
        self.assertEqual(buy_in.settings_version.number, 1)
        self.assertFalse(hasattr(buy_in, "chips"))

    def test_several_rebuys_give_a_running_total(self):
        night = Night("A", "B")
        night.buy("A", 1000)
        night.buy("A", 500)
        night.buy("A", 2000)
        night.buy("B", 1000)
        summary = queries.summary(night.session)
        line = summary.line_for(night.players["A"].pk)
        self.assertEqual((line.buy_in_count, line.rebuy_count, line.buy_in_total), (3, 2, 350000))
        self.assertEqual(line.initial_buy_in.amount, 100000)
        self.assertEqual((summary.player_count, summary.buy_in_count, summary.total), (2, 4, 450000))

    def test_fixed_amount_total_equals_count_times_amount(self):
        night = Night("A", "B", "C")
        for name in ("A", "B", "C", "A", "B"):
            night.buy(name, 1000)
        summary = queries.summary(night.session)
        self.assertEqual(summary.total, summary.buy_in_count * 100000)

    def test_amount_outside_the_range_is_refused(self):
        night = Night("A")
        for pesos in (499, 2001):
            with self.assertRaisesMessage(RuleError, "between ₱500 and ₱2,000"):
                night.buy("A", pesos)
        self.assertEqual(BuyIn.objects.count(), 0)

    def test_any_amount_inside_the_range_is_accepted(self):
        night = Night("A")
        buy_in = services.record_buy_in(night.session.pk, night.host, night.players["A"].pk, 123456, uuid.uuid4())
        self.assertEqual(buy_in.amount, 123456)  # ₱1,234.56: no chip rule applies

    def test_amount_must_be_an_integer(self):
        night = Night("A")
        for bad in (1000.0, "100000", None, True):
            with self.assertRaises(RuleError):
                services.record_buy_in(night.session.pk, night.host, night.players["A"].pk, bad, uuid.uuid4())

    def test_repeated_request_id_records_once(self):
        night = Night("A")
        request_id = uuid.uuid4()
        first = night.buy("A", 1000, request_id)
        second = night.buy("A", 1000, request_id)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(BuyIn.objects.count(), 1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            BuyIn.objects.create(
                session=night.session, participant=night.players["A"], settings_version=first.settings_version,
                amount=1, request_id=request_id, recorded_by=night.host.user,
            )

    def test_only_a_host_records_and_only_in_open_or_running(self):
        night = Night("A", state="open")
        ben = night.add_login_player("ben")
        with self.assertRaises(NotAllowed):
            services.record_buy_in(night.session.pk, ben, night.players["ben"].pk, 100000, uuid.uuid4())
        night.buy("A", 1000)  # open: allowed
        night.go("reconciliation")
        with self.assertRaises(RuleError):
            night.buy("A", 1000)

    def test_player_must_be_at_the_table(self):
        night = Night("A", "B")
        games.set_left(night.session.pk, night.host, night.players["A"].pk)
        with self.assertRaises(RuleError):
            night.buy("A", 1000)
        with self.assertRaises(RuleError):
            services.record_buy_in(night.session.pk, night.host, 999999, 100000, uuid.uuid4())

    def test_changed_settings_apply_to_new_buy_ins_only(self):
        night = Night("A")
        first = night.buy("A", 1000)
        games.update_settings(night.session.pk, night.host, {**STAKES, "max_buy_in": 500000})
        second = night.buy("A", 5000)
        first.refresh_from_db()
        self.assertEqual((first.amount, first.settings_version.number), (100000, 1))
        self.assertEqual((second.amount, second.settings_version.number), (500000, 2))

    def test_preset_edit_rewrites_no_buy_in(self):
        night = Night("A")
        preset = make_preset(night.host)
        buy_in = night.buy("A", 1000)
        games.save_preset(night.host, {"name": "10/20", "game_type": "nlh", **STAKES, "default_buy_in": 150000}, preset_id=preset.pk)
        buy_in.refresh_from_db()
        self.assertEqual(buy_in.amount, 100000)


class ReversalTests(TestCase):
    def test_reversal_restores_totals_and_keeps_the_row(self):
        night = Night("A", "B")
        night.buy("A", 1000)
        wrong = night.buy("B", 1000)
        night.buy("B", 1000)
        services.reverse_buy_in(night.session.pk, night.host, wrong.pk, "recorded twice")
        summary = queries.summary(night.session)
        line = summary.line_for(night.players["B"].pk)
        self.assertEqual((summary.total, summary.buy_in_count), (200000, 2))
        self.assertEqual([b.pk for b in line.reversed_buy_ins], [wrong.pk])
        self.assertEqual(BuyIn.objects.count(), 3)  # nothing is deleted
        wrong.refresh_from_db()
        self.assertEqual(wrong.amount, 100000)  # nothing is rewritten
        event = AuditEvent.objects.get(action="buy_in.reversed")
        self.assertEqual(event.reason, "recorded twice")

    def test_reason_is_required_and_reversing_twice_changes_nothing(self):
        night = Night("A")
        buy_in = night.buy("A", 1000)
        with self.assertRaises(RuleError):
            services.reverse_buy_in(night.session.pk, night.host, buy_in.pk, "  ")
        first = services.reverse_buy_in(night.session.pk, night.host, buy_in.pk, "wrong player")
        again = services.reverse_buy_in(night.session.pk, night.host, buy_in.pk, "other words")
        self.assertEqual(first.pk, again.pk)
        self.assertEqual(BuyInReversal.objects.count(), 1)

    def test_game_with_buy_ins_cannot_be_canceled_until_they_are_reversed(self):
        night = Night("A")
        buy_in = night.buy("A", 1000)
        self.assertTrue(games.has_money(night.session))
        with self.assertRaises(RuleError):
            games.transition(night.session.pk, night.host, "cancel", "rain")
        services.reverse_buy_in(night.session.pk, night.host, buy_in.pk, "game called off")
        self.assertFalse(games.has_money(night.session))
        self.assertEqual(games.transition(night.session.pk, night.host, "cancel", "rain").state, "canceled")

    def test_player_with_buy_ins_cannot_be_withdrawn(self):
        night = Night("A", state="open")
        buy_in = night.buy("A", 1000)
        with self.assertRaisesMessage(RuleError, "has buy-ins"):
            games.withdraw_participant(night.session.pk, night.host, night.players["A"].pk)
        services.reverse_buy_in(night.session.pk, night.host, buy_in.pk, "did not play")
        games.withdraw_participant(night.session.pk, night.host, night.players["A"].pk)
        self.assertEqual(queries.summary(night.session).player_count, 0)

    def test_only_a_host_reverses(self):
        night = Night("A")
        ben = night.add_login_player("ben")
        buy_in = night.buy("A", 1000)
        with self.assertRaises(NotAllowed):
            services.reverse_buy_in(night.session.pk, ben, buy_in.pk, "x")


class BuyInViewTests(TestCase):
    def setUp(self):
        self.night = Night("A")
        self.ben = self.night.add_login_player("ben")
        self.url = reverse("buy_in_add", args=[self.night.session.pk])

    def _post(self, **data):
        return self.client.post(self.url, {"participant_id": self.night.players["A"].pk, "amount": "1,000", **data}, follow=True)

    def test_host_records_and_page_shows_totals_in_pesos_only(self):
        self.client.force_login(self.night.host.user)
        self._post()
        page = self._post(amount="500")
        self.assertContains(page, "₱1,500")
        self.assertContains(page, "1 buy-in + 1 rebuy")
        self.assertContains(page, "Still in play")
        self.assertNotContains(page, "chips")  # a pesos game shows no chip figure

    def test_double_submit_of_one_form_records_once(self):
        self.client.force_login(self.night.host.user)
        request_id = str(uuid.uuid4())
        self._post(request_id=request_id)
        self._post(request_id=request_id)
        self.assertEqual(BuyIn.objects.count(), 1)

    def test_bad_amounts_show_a_message(self):
        self.client.force_login(self.night.host.user)
        self.assertContains(self._post(amount="abc"), "Enter an amount in pesos")
        self.assertContains(self._post(amount="100"), "between ₱500 and ₱2,000")
        self.assertEqual(BuyIn.objects.count(), 0)

    def test_player_and_stranger_are_refused(self):
        buy_in = self.night.buy("A", 1000)
        reverse_url = reverse("buy_in_reverse", args=[self.night.session.pk, buy_in.pk])
        self.client.force_login(self.ben.user)
        self.assertEqual(self.client.post(self.url, {"participant_id": self.night.players["ben"].pk, "amount": "1000"}).status_code, 403)
        self.assertEqual(self.client.post(reverse_url, {"reason": "x"}).status_code, 403)
        page = self.client.get(reverse("session", args=[self.night.session.pk]))
        self.assertNotContains(page, "buyins/add")
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.post(self.url, {"amount": "1000"}).status_code, 404)
        self.assertEqual(self.client.post(reverse_url, {"reason": "x"}).status_code, 404)
        self.assertEqual(BuyIn.objects.count(), 1)
        self.assertEqual(BuyInReversal.objects.count(), 0)
