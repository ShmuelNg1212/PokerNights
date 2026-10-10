import uuid

from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player
from ledger import queries, services
from ledger.models import BalanceAdjustment, BuyIn, CashOut

from .helpers import Night


def worked_example(cash=(1600, 700, 200)):
    """A buys in ₱1,000, B ₱1,000, C ₱500. Cash-outs in pesos. The game is in the counting stage."""
    night = Night("A", "B", "C")
    night.buy("A", 1000)
    night.buy("B", 1000)
    night.buy("C", 500)
    night.go("reconciliation")
    for name, pesos in zip("ABC", cash):
        if pesos is not None:
            night.cash(name, pesos)
    return night


def override(night, mode="player", name="A", note="could not find it"):
    participant_id = night.players[name].pk if mode == "player" else None
    return services.record_override(night.session.pk, night.host, note, mode, participant_id, uuid.uuid4())


class BalanceCheckTests(TestCase):
    def test_balanced_session(self):
        balance = queries.balance(worked_example().session)
        self.assertTrue(balance.ok)
        self.assertEqual((balance.difference, balance.direction, balance.explanation), (0, "", ""))

    def test_small_surplus_shows_amount_and_direction(self):
        balance = queries.balance(worked_example((1600, 700, 250)).session)
        self.assertFalse(balance.ok)
        self.assertEqual((balance.difference, balance.direction, balance.difference_text), (5000, "extra", "₱50"))
        self.assertIn("₱50 too much", balance.explanation)
        self.assertIn("buy-in that was not recorded", balance.explanation)

    def test_small_shortfall_shows_amount_and_direction(self):
        balance = queries.balance(worked_example((1600, 700, 150)).session)
        self.assertEqual((balance.difference, balance.direction), (-5000, "missing"))
        self.assertIn("₱50 is missing", balance.explanation)
        self.assertIn("recorded twice", balance.explanation)

    def test_missing_cash_out_is_named_and_not_treated_as_zero(self):
        balance = queries.balance(worked_example((1600, 900, None)).session)
        self.assertFalse(balance.ok)
        self.assertFalse(balance.counted)
        self.assertIn("Not cashed out yet: C", balance.explanation)

    def test_cash_out_without_a_buy_in_is_flagged(self):
        night = worked_example()
        buy_in = BuyIn.objects.get(participant=night.players["C"])
        services.reverse_buy_in(night.session.pk, night.host, buy_in.pk, "did not pay")
        balance = queries.balance(night.session)
        self.assertFalse(balance.ok)
        self.assertIn("C has a cash-out but no buy-in", balance.explanation)

    def test_nothing_is_adjusted_automatically(self):
        night = worked_example((1600, 700, 250))
        queries.balance(night.session)
        self.assertEqual(BalanceAdjustment.objects.count(), 0)
        self.assertEqual(list(CashOut.objects.order_by("id").values_list("amount", flat=True)), [160000, 70000, 25000])

    def test_duplicate_buy_in_is_found_and_fixed_by_reversal(self):
        night = Night("A", "B")
        night.buy("A", 1000)
        night.buy("B", 1000)
        twice = night.buy("B", 1000)
        night.go("reconciliation")
        night.cash("A", 1400)
        night.cash("B", 600)
        self.assertEqual(queries.balance(night.session).difference, -100000)
        services.reverse_buy_in(night.session.pk, night.host, twice.pk, "recorded twice")
        self.assertTrue(queries.balance(night.session).ok)


class OverrideTests(TestCase):
    def test_named_player_absorbs_a_surplus(self):
        night = worked_example((1600, 700, 250))
        rows = override(night, name="A", note="someone was overpaid")
        self.assertEqual([(r.participant_id, r.amount) for r in rows], [(night.players["A"].pk, -5000)])
        balance = queries.balance(night.session)
        self.assertTrue(balance.ok)
        self.assertTrue(balance.overridden)
        self.assertEqual(night.line("A").cash_out_final, 155000)
        event = AuditEvent.objects.get(action="balance.overridden")
        self.assertEqual(event.reason, "someone was overpaid")

    def test_named_player_absorbs_a_shortfall(self):
        night = worked_example((1600, 700, 150))
        override(night, name="B")
        self.assertEqual(night.line("B").cash_out_final, 75000)
        self.assertTrue(queries.balance(night.session).ok)

    def test_equal_share_that_does_not_divide_evenly(self):
        night = worked_example((1600, 700, 250))  # ₱50 too much among 3 players: 5,000 centavos
        rows = override(night, mode="equal")
        self.assertEqual([r.amount for r in rows], [-1667, -1667, -1666])
        self.assertEqual(sum(r.amount for r in rows), -5000)
        self.assertTrue(queries.balance(night.session).ok)

    def test_equal_share_skips_zero_parts(self):
        night = worked_example((1600, 700, None))
        services.record_cash_out(night.session.pk, night.host, night.players["C"].pk, 20001, uuid.uuid4())  # 1 centavo too much
        rows = override(night, mode="equal")
        self.assertEqual([(r.participant_id, r.amount) for r in rows], [(night.players["A"].pk, -1)])

    def test_note_and_absorber_are_required(self):
        night = worked_example((1600, 700, 250))
        with self.assertRaisesMessage(RuleError, "note"):
            override(night, note="   ")
        with self.assertRaises(RuleError):
            services.record_override(night.session.pk, night.host, "note", "player", 999999, uuid.uuid4())
        with self.assertRaises(RuleError):
            services.record_override(night.session.pk, night.host, "note", "house", None, uuid.uuid4())
        self.assertEqual(BalanceAdjustment.objects.count(), 0)

    def test_refused_when_balanced_or_not_fully_counted(self):
        with self.assertRaisesMessage(RuleError, "No override is needed"):
            override(worked_example())
        with self.assertRaisesMessage(RuleError, "Not cashed out yet: C"):
            override(worked_example((1600, 700, None)))

    def test_only_a_host_and_only_while_counting(self):
        night = worked_example((1600, 700, 250))
        running = Night("X")
        running.buy("X", 1000)
        running.cash("X", 900)
        with self.assertRaises(RuleError):
            override(running, name="X")
        player = add_player(night.group, "ben")
        with self.assertRaises(NotAllowed):
            services.record_override(night.session.pk, player, "note", "equal", None, uuid.uuid4())

    def test_repeated_request_records_once(self):
        night = worked_example((1600, 700, 250))
        request_id = uuid.uuid4()
        for _ in range(2):
            services.record_override(night.session.pk, night.host, "note", "equal", None, request_id)
        self.assertEqual(BalanceAdjustment.objects.count(), 3)

    def test_a_later_correction_reopens_the_difference_and_the_override_can_be_removed(self):
        night = worked_example((1600, 700, 250))
        override(night)
        wrong = CashOut.objects.get(participant=night.players["C"])
        services.reverse_cash_out(night.session.pk, night.host, wrong.pk, "recount")
        night.cash("C", 260)  # a late find: the books are off again
        self.assertEqual(queries.balance(night.session).difference, 1000)
        self.assertEqual(services.void_override(night.session.pk, night.host), 1)
        self.assertEqual(queries.balance(night.session).difference, 6000)
        self.assertEqual(BalanceAdjustment.objects.count(), 1)  # the row stays, marked void


class BalanceViewTests(TestCase):
    def test_page_explains_the_mismatch_and_host_records_an_override(self):
        night = worked_example((1600, 700, 250))
        self.client.force_login(night.host.user)
        page = self.client.get(reverse("session", args=[night.session.pk]))
        self.assertContains(page, "₱50 too much")
        self.assertContains(page, "Finalize with an override")
        self.assertContains(page, "Total cashed out")
        self.assertNotContains(page, "Still in play")  # a negative "in play" figure would mislead
        page = self.client.post(reverse("override_add", args=[night.session.pk]), {"absorber": "equal", "note": "old chips mixed in"}, follow=True)
        self.assertContains(page, "A host override covers the difference")
        self.assertContains(page, "old chips mixed in")
        page = self.client.post(reverse("override_void", args=[night.session.pk]), follow=True)
        self.assertContains(page, "₱50 too much")

    def test_player_sees_the_check_but_cannot_override(self):
        night = worked_example((1600, 700, 250))
        player = add_player(night.group, "ben")
        self.client.force_login(player.user)
        page = self.client.get(reverse("session", args=[night.session.pk]))
        self.assertContains(page, "The books")
        self.assertNotContains(page, "Record override")
        self.assertEqual(self.client.post(reverse("override_add", args=[night.session.pk]), {"absorber": "equal", "note": "x"}).status_code, 403)
        self.assertEqual(self.client.post(reverse("override_void", args=[night.session.pk])).status_code, 403)
