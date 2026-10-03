import uuid

from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from groups.errors import NotAllowed, RuleError
from groups.tests.helpers import add_player
from ledger import queries, services
from ledger.models import BalanceAdjustment, BuyIn, CashOut

from .helpers import Night


def worked_example(cash=(16000, 7000, 2000)):
    """A ₱1,000, B ₱1,000, C ₱500 at ₱1,000 per 10,000 chips, in the counting stage."""
    night = Night("A", "B", "C")
    night.buy("A", 1000)
    night.buy("B", 1000)
    night.buy("C", 500)
    night.go("reconciliation")
    for name, chips in zip("ABC", cash):
        if chips is not None:
            night.cash(name, chips)
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
        balance = queries.balance(worked_example((16000, 7000, 2500)).session)
        self.assertFalse(balance.ok)
        self.assertEqual((balance.difference, balance.direction, balance.difference_value), (500, "extra", "₱50"))
        self.assertIn("500 chips (₱50) extra", balance.explanation)
        self.assertIn("buy-in that was not recorded", balance.explanation)

    def test_small_shortfall_shows_amount_and_direction(self):
        balance = queries.balance(worked_example((16000, 7000, 1500)).session)
        self.assertEqual((balance.difference, balance.direction), (-500, "missing"))
        self.assertIn("500 chips (₱50) missing", balance.explanation)
        self.assertIn("recorded twice", balance.explanation)

    def test_missing_cash_out_is_named_and_not_treated_as_zero(self):
        balance = queries.balance(worked_example((16000, 9000, None)).session)
        self.assertFalse(balance.ok)
        self.assertFalse(balance.counted)
        self.assertIn("No cash-out is recorded for: C", balance.explanation)

    def test_cash_out_without_a_buy_in_is_flagged(self):
        night = worked_example()
        buy_in = BuyIn.objects.get(participant=night.players["C"])
        services.reverse_buy_in(night.session.pk, night.host, buy_in.pk, "did not pay")
        balance = queries.balance(night.session)
        self.assertFalse(balance.ok)
        self.assertIn("C cashed out chips but has no buy-in", balance.explanation)

    def test_nothing_is_adjusted_automatically(self):
        night = worked_example((16000, 7000, 2500))
        queries.balance(night.session)
        self.assertEqual(BalanceAdjustment.objects.count(), 0)
        self.assertEqual(list(CashOut.objects.order_by("id").values_list("chips", flat=True)), [16000, 7000, 2500])

    def test_duplicate_buy_in_is_found_and_fixed_by_reversal(self):
        night = Night("A", "B")
        night.buy("A", 1000)
        night.buy("B", 1000)
        twice = night.buy("B", 1000)
        night.go("reconciliation")
        night.cash("A", 14000)
        night.cash("B", 6000)
        self.assertEqual(queries.balance(night.session).difference, -10000)
        services.reverse_buy_in(night.session.pk, night.host, twice.pk, "recorded twice")
        self.assertTrue(queries.balance(night.session).ok)


class OverrideTests(TestCase):
    def test_named_player_absorbs_a_surplus(self):
        night = worked_example((16000, 7000, 2500))
        rows = override(night, name="A", note="extra chips from another set")
        self.assertEqual([(r.participant_id, r.chips_delta) for r in rows], [(night.players["A"].pk, -500)])
        balance = queries.balance(night.session)
        self.assertTrue(balance.ok)
        self.assertTrue(balance.overridden)
        self.assertEqual(night.line("A").chips_final, 15500)
        event = AuditEvent.objects.get(action="balance.overridden")
        self.assertEqual(event.reason, "extra chips from another set")

    def test_named_player_absorbs_a_shortfall(self):
        night = worked_example((16000, 7000, 1500))
        override(night, name="B")
        self.assertEqual(night.line("B").chips_final, 7500)
        self.assertTrue(queries.balance(night.session).ok)

    def test_equal_share_that_does_not_divide_evenly(self):
        night = worked_example((16000, 7000, 2500))  # 500 extra among 3 players
        rows = override(night, mode="equal")
        self.assertEqual([r.chips_delta for r in rows], [-167, -167, -166])
        self.assertEqual(sum(r.chips_delta for r in rows), -500)
        self.assertTrue(queries.balance(night.session).ok)

    def test_equal_share_skips_zero_parts(self):
        night = worked_example((16000, 7000, 2001))  # 1 extra chip among 3 players
        rows = override(night, mode="equal")
        self.assertEqual([(r.participant_id, r.chips_delta) for r in rows], [(night.players["A"].pk, -1)])

    def test_note_and_absorber_are_required(self):
        night = worked_example((16000, 7000, 2500))
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
        with self.assertRaisesMessage(RuleError, "No cash-out is recorded for: C"):
            override(worked_example((16000, 7000, None)))

    def test_only_a_host_and_only_while_counting(self):
        night = worked_example((16000, 7000, 2500))
        running = Night("X")
        running.buy("X", 1000)
        running.cash("X", 9000)
        with self.assertRaises(RuleError):
            override(running, name="X")
        player = add_player(night.group, "ben")
        with self.assertRaises(NotAllowed):
            services.record_override(night.session.pk, player, "note", "equal", None, uuid.uuid4())

    def test_repeated_request_records_once(self):
        night = worked_example((16000, 7000, 2500))
        request_id = uuid.uuid4()
        for _ in range(2):
            services.record_override(night.session.pk, night.host, "note", "equal", None, request_id)
        self.assertEqual(BalanceAdjustment.objects.count(), 3)

    def test_a_later_correction_reopens_the_difference_and_the_override_can_be_removed(self):
        night = worked_example((16000, 7000, 2500))
        override(night)
        night.cash("C", 100)  # a late find: the books are off again
        self.assertEqual(queries.balance(night.session).difference, 100)
        self.assertEqual(services.void_override(night.session.pk, night.host), 1)
        self.assertEqual(queries.balance(night.session).difference, 600)
        self.assertEqual(BalanceAdjustment.objects.count(), 1)  # the row stays, marked void


class BalanceViewTests(TestCase):
    def test_page_explains_the_mismatch_and_host_records_an_override(self):
        night = worked_example((16000, 7000, 2500))
        self.client.force_login(night.host.user)
        page = self.client.get(reverse("session", args=[night.session.pk]))
        self.assertContains(page, "500 chips (₱50) extra")
        self.assertContains(page, "Finalize with an override")
        page = self.client.post(reverse("override_add", args=[night.session.pk]), {"absorber": "equal", "note": "old chips mixed in"}, follow=True)
        self.assertContains(page, "A host override covers the difference")
        self.assertContains(page, "old chips mixed in")
        page = self.client.post(reverse("override_void", args=[night.session.pk]), follow=True)
        self.assertContains(page, "500 chips (₱50) extra")

    def test_player_sees_the_check_but_cannot_override(self):
        night = worked_example((16000, 7000, 2500))
        player = add_player(night.group, "ben")
        self.client.force_login(player.user)
        page = self.client.get(reverse("session", args=[night.session.pk]))
        self.assertContains(page, "Balance check")
        self.assertNotContains(page, "Record override")
        self.assertEqual(self.client.post(reverse("override_add", args=[night.session.pk]), {"absorber": "equal", "note": "x"}).status_code, 403)
        self.assertEqual(self.client.post(reverse("override_void", args=[night.session.pk])).status_code, 403)
