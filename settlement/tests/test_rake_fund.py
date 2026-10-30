"""The rake fund: a group may settle collected rake into the fund instead of returning it to each player."""

import uuid

from django.db import IntegrityError, transaction
from django.test import TestCase

from audit.models import AuditEvent
from games import services as games
from groups import services as groups
from groups.errors import NotAllowed
from groups.models import GroupRakeAccount
from ledger.tests.helpers import Night
from ledger.tests.test_rake import configure
from settlement import queries, services as settle
from settlement.models import Transfer


def finish(n, **cash):
    n.go("reconciliation")
    for name, amount in cash.items():
        n.cash(name, amount)
    return settle.finalize(n.session.pk, n.host)


def raked(*names, unit="php", **rule):
    n = Night(*names, unit=unit)
    configure(n, **(rule or {"rake_mode": "percent", "rake_basis_points": 500}))
    return n


def to_fund(n):
    groups.set_rake_settlement(n.host, GroupRakeAccount.Settlement.FUND)


def rows(plan):
    return [(t.payer_id, t.payee_id, t.to_rake_fund, t.amount) for t in plan.transfers.order_by("position")]


class RakeSettlementOptionTests(TestCase):
    def test_default_returns_rake_to_each_player(self):
        n = raked("A", "B")
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=1400, B=500)
        plan = settle.close_night(n.session.night_id, n.host)
        a, b = n.players["A"].member_id, n.players["B"].member_id
        self.assertEqual(rows(plan), [(b, a, False, 45000)])
        self.assertFalse(plan.rake_to_fund)

    def test_only_a_host_changes_it_and_a_repeat_writes_nothing(self):
        n = Night("A")
        member = n.add_login_player("P")
        with self.assertRaises(NotAllowed):
            groups.set_rake_settlement(member, "fund")
        to_fund(n)
        to_fund(n)
        self.assertEqual(n.group.rake_account.__class__.objects.get(group=n.group).settlement, "fund")
        self.assertEqual(AuditEvent.objects.filter(action="group.rake_settlement").count(), 1)

    def test_unknown_choice_is_refused(self):
        from groups.errors import RuleError

        n = Night("A")
        with self.assertRaises(RuleError):
            groups.set_rake_settlement(n.host, "split")

    def test_a_group_without_an_account_gets_one(self):
        n = Night("A")
        GroupRakeAccount.objects.filter(group=n.group).delete()
        to_fund(n)
        self.assertEqual(GroupRakeAccount.objects.get(group=n.group).settlement, "fund")


class RakeFundTests(TestCase):
    def test_settle_up_equals_the_standings_and_the_fund_gets_the_rake(self):
        n = raked("A", "B")
        to_fund(n)
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=1400, B=500)
        plan = settle.close_night(n.session.night_id, n.host)
        a, b = n.players["A"].member_id, n.players["B"].member_id
        self.assertTrue(plan.rake_to_fund)
        self.assertCountEqual(rows(plan), [(b, a, False, 40000), (b, None, True, 10000)])
        found = queries.night_outcome(n.session.night)
        self.assertEqual({s.pk: s.settlement_balance for s in found.standings}, {a: 40000, b: -50000})
        self.assertEqual({s.pk: s.net for s in found.standings}, {a: 40000, b: -50000})
        fund = next(t for t in found.transfers if t.to_rake_fund)
        self.assertEqual(fund.payee_label, "Rake fund")
        self.assertIsNone(fund.payee_token)

    def test_equal_fee_only_losses_pay_the_fund(self):
        n = raked("A", "B")
        to_fund(n)
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=950, B=950)
        plan = settle.close_night(n.session.night_id, n.host)
        a, b = n.players["A"].member_id, n.players["B"].member_id
        self.assertCountEqual(rows(plan), [(a, None, True, 5000), (b, None, True, 5000)])

    def test_several_sets_add_their_rake(self):
        n = raked("A", "B", rake_mode="flat", rake_flat=2000)
        to_fund(n)
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=1480, B=480)
        second = games.start_next_set(n.session.night_id, n.host)
        players = {p.member.display_name: p for p in second.participants.select_related("member")}
        from ledger import services as ledger

        for p in players.values():
            ledger.record_buy_in(second.pk, n.host, p.pk, 100000, uuid.uuid4())
        games.transition(second.pk, n.host, "start", opening_buy_ins=False)
        games.transition(second.pk, n.host, "end")
        ledger.record_cash_out(second.pk, n.host, players["A"].pk, 88000, uuid.uuid4())
        ledger.record_cash_out(second.pk, n.host, players["B"].pk, 108000, uuid.uuid4())
        settle.finalize(second.pk, n.host)
        plan = settle.close_night(n.session.night_id, n.host)
        # A: +500 − 120 = +380; B: −520 + 80 = −440; rake 4 × ₱20 = ₱80.
        fund = plan.transfers.get(to_rake_fund=True)
        self.assertEqual(fund.amount, 8000)
        self.assertEqual(sum(t.amount for t in plan.transfers.all()), 44000)

    def test_chips_game(self):
        n = raked("A", "B", unit="chips", rake_mode="flat", rake_flat=10)
        to_fund(n)
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=1200, B=780)
        plan = settle.close_night(n.session.night_id, n.host)
        self.assertEqual(plan.transfers.get(to_rake_fund=True).amount, 20)

    def test_no_rake_no_fund_line(self):
        n = Night("A", "B")
        to_fund(n)
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=1500, B=500)
        plan = settle.close_night(n.session.night_id, n.host)
        self.assertFalse(plan.transfers.filter(to_rake_fund=True).exists())
        self.assertTrue(plan.rake_to_fund)

    def test_a_closed_session_keeps_its_list_and_a_reclose_uses_the_option(self):
        n = raked("A", "B")
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=1400, B=500)
        first = settle.close_night(n.session.night_id, n.host)
        to_fund(n)
        first.refresh_from_db()
        self.assertFalse(first.transfers.filter(to_rake_fund=True).exists())
        # The page of a session closed under the old rule still reads it.
        found = queries.night_outcome(n.session.night)
        b = n.players["B"].member_id
        self.assertEqual(found.standing_for(b).settlement_balance, -45000)
        settle.reopen_night(n.session.night_id, n.host, "fix")
        second = settle.close_night(n.session.night_id, n.host)
        self.assertTrue(second.transfers.filter(to_rake_fund=True).exists())

    def test_mark_paid_and_undo_on_a_fund_transfer(self):
        n = raked("A", "B")
        to_fund(n)
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=1400, B=500)
        plan = settle.close_night(n.session.night_id, n.host)
        fund = plan.transfers.get(to_rake_fund=True)
        payment = settle.mark_paid(n.session.night_id, n.host, fund.pk, uuid.uuid4())
        self.assertIsNone(payment.payee_id)
        self.assertIn("Rake fund", AuditEvent.objects.filter(action="transfer.paid").last().summary)
        settle.mark_unpaid(n.session.night_id, n.host, fund.pk)
        found = queries.night_outcome(n.session.night)
        self.assertFalse(next(t for t in found.transfers if t.to_rake_fund).paid)

    def test_a_fund_transfer_is_never_carried(self):
        n = raked("A", "B")
        to_fund(n)
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=1400, B=500)
        settle.close_night(n.session.night_id, n.host)
        later = Night.__new__(Night)
        later.group, later.host, later.scale = n.group, n.host, 100
        from games.tests.helpers import make_session

        later.session = make_session(n.host, table=n.session.table, state="open")
        later.players = {}
        for name in ("A", "B"):
            later.players[name] = games.add_participant(later.session.pk, n.host, n.players[name].member_id)
        later.go("running")
        later.buy("A", 1000); later.buy("B", 1000)
        finish(later, A=1000, B=1000)
        carryable = queries.carryable(later.session.night)
        self.assertTrue(carryable)
        self.assertFalse(any(t.to_rake_fund for t in carryable))

    def test_the_database_refuses_a_transfer_with_two_payees_or_none(self):
        n = raked("A", "B")
        to_fund(n)
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=1400, B=500)
        plan = settle.close_night(n.session.night_id, n.host)
        b = n.players["B"].member_id
        with self.assertRaises(IntegrityError), transaction.atomic():
            Transfer.objects.create(plan=plan, position=9, payer_id=b, payee=None, to_rake_fund=False, amount=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Transfer.objects.create(plan=plan, position=9, payer_id=b, payee_id=n.players["A"].member_id,
                                    to_rake_fund=True, amount=1)


class RakeFundPageTests(TestCase):
    def test_a_host_saves_the_rule_from_group_settings_and_a_player_cannot(self):
        n = Night("A")
        url = f"/g/{n.group.pk}/rake/"
        player = n.add_login_player("P")
        self.client.force_login(player.user)
        self.client.post(url, {"settlement": "fund"})
        self.assertEqual(GroupRakeAccount.objects.get(group=n.group).settlement, "returned")
        page = self.client.get(f"/g/{n.group.pk}/?view=settings")
        self.assertContains(page, "Players pay the rake in cash at buy-in.")
        self.client.force_login(n.host.user)
        self.client.post(url, {"settlement": "fund"})
        self.assertEqual(GroupRakeAccount.objects.get(group=n.group).settlement, "fund")
        page = self.client.get(f"/g/{n.group.pk}/?view=settings")
        self.assertContains(page, 'value="fund" checked')

    def test_the_settle_up_page_names_the_rake_fund(self):
        n = raked("A", "B")
        to_fund(n)
        n.buy("A", 1000); n.buy("B", 1000)
        finish(n, A=1400, B=500)
        settle.close_night(n.session.night_id, n.host)
        self.client.force_login(n.host.user)
        page = self.client.get(f"/n/{n.session.night_id}/")
        self.assertContains(page, "Rake fund")
        self.assertContains(page, "chip-fund")
