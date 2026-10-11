"""Unpaid transfers of earlier sessions folded into a later session's list when it is closed."""

import uuid

from django.test import TestCase, override_settings

from audit.models import AuditEvent
from games import services as games
from games.tests.helpers import CHIP_STAKES, make_session
from groups import services as groups
from groups.errors import RuleError
from groups.tests.helpers import make_group
from ledger import services as ledger
from settlement import queries, services
from settlement.models import CarriedTransfer, SettlementPlan, Transfer


class Club:
    """One group whose sessions are played to given results. Amounts are whole pesos (or chips)."""

    def __init__(self, *names):
        self.group, self.host = make_group()
        self.members = {name: groups.add_roster_player(self.host, name) for name in names}
        self.tables = 0

    def play(self, nets: dict, *, unit="php"):
        """A session where each named player ends with this result. Finalized, not closed. Returns its id."""
        assert sum(nets.values()) == 0
        self.tables += 1
        stakes = {**CHIP_STAKES, "unit": "chips"} if unit == "chips" else {}
        scale = 1 if unit == "chips" else 100
        session = make_session(self.host, state="open", table_name=f"Table {self.tables}", **stakes)
        seats = {name: games.add_participant(session.pk, self.host, self.members[name].pk) for name in nets}
        for name in nets:
            ledger.record_buy_in(session.pk, self.host, seats[name].pk, 1000 * scale, uuid.uuid4())
        games.transition(session.pk, self.host, "start", opening_buy_ins=False)
        games.transition(session.pk, self.host, "end")
        for name, net in nets.items():
            ledger.record_cash_out(session.pk, self.host, seats[name].pk, (1000 + net) * scale, uuid.uuid4())
        services.finalize(session.pk, self.host)
        return session.night_id

    def close(self, night_id, carry=()):
        return services.close_night(night_id, self.host, [t.pk for t in carry])

    def closed(self, nets, **options):
        night_id = self.play(nets, **options)
        self.close(night_id)
        return night_id

    def transfers(self, night_id):
        """``{(payer, payee): pesos}`` of the session's current list."""
        names = {member.pk: name for name, member in self.members.items()}
        rows = Transfer.objects.filter(plan__night_id=night_id, plan__is_current=True).order_by("position")
        return {(names[t.payer_id], names[t.payee_id]): t.amount // 100 for t in rows}

    def unpaid(self, night_id):
        return list(Transfer.objects.filter(plan__night_id=night_id, plan__is_current=True).order_by("position"))

    def owed(self):
        """Each person's net over every unpaid transfer in the group: what they are owed minus what they owe."""
        totals = {name: 0 for name in self.members}
        names = {member.pk: name for name, member in self.members.items()}
        for transfer in queries.unpaid_transfers([member.pk for member in self.members.values()]):
            totals[names[transfer.payer_id]] -= transfer.amount
            totals[names[transfer.payee_id]] += transfer.amount
        return totals


class CarryTests(TestCase):
    def setUp(self):
        self.club = Club("Ana", "Ben", "Carlo", "Dee")
        self.first = self.club.closed({"Ana": -500, "Ben": 500})  # Ana owes Ben 500
        self.old = self.club.unpaid(self.first)

    def test_nothing_is_carried_unless_asked(self):
        second = self.club.closed({"Ana": 300, "Ben": -300})
        self.assertEqual(self.club.transfers(second), {("Ben", "Ana"): 300})
        self.assertEqual(CarriedTransfer.objects.count(), 0)
        self.assertEqual(len(queries.unpaid_transfers([m.pk for m in self.club.members.values()])), 2)

    def test_a_debt_and_tonights_result_cancel_to_nothing(self):
        second = self.club.play({"Ana": 500, "Ben": -500})
        self.assertEqual([t.pk for t in queries.carryable(self.club.host.group.nights.get(pk=second))], [self.old[0].pk])
        self.club.close(second, self.old)
        self.assertEqual(self.club.transfers(second), {})
        self.assertEqual(queries.settle_states([self.first, second])[self.first].status, "settled")
        self.assertEqual(queries.settle_states([self.first, second])[second].status, "settled")
        self.assertEqual(self.club.owed(), {"Ana": 0, "Ben": 0, "Carlo": 0, "Dee": 0})

    def test_a_debt_is_added_to_tonights_result(self):
        second = self.club.play({"Ana": -200, "Ben": 200})
        self.club.close(second, self.old)
        self.assertEqual(self.club.transfers(second), {("Ana", "Ben"): 700})

    def test_the_netted_list_can_change_who_pays_whom(self):
        second = self.club.play({"Ana": 0, "Ben": -500, "Carlo": 500})
        self.club.close(second, self.old)
        self.assertEqual(self.club.transfers(second), {("Ana", "Carlo"): 500})

    def test_what_everyone_owes_over_all_sessions_is_the_same_before_and_after(self):
        other = self.club.closed({"Carlo": -300, "Dee": 300})
        second = self.club.play({"Ana": 100, "Ben": -400, "Carlo": 250, "Dee": 50})
        plain = dict(services.settlement_balances(self.club.host.group.nights.get(pk=second)))
        before = self.club.owed()
        for member_id, balance in plain.items():
            name = next(n for n, m in self.club.members.items() if m.pk == member_id)
            before[name] += balance
        self.club.close(second, self.old + self.club.unpaid(other))
        self.assertEqual(self.club.owed(), before)
        self.assertEqual(sum(self.club.owed().values()), 0)

    def test_only_ticked_transfers_are_carried(self):
        other = self.club.closed({"Ana": -100, "Carlo": 100})
        second = self.club.play({"Ana": 0, "Ben": 0, "Carlo": 0})
        self.club.close(second, self.club.unpaid(other))
        self.assertEqual(self.club.transfers(second), {("Ana", "Carlo"): 100})
        outcome = queries.night_outcome(self.club.host.group.nights.get(pk=self.first))
        self.assertIsNone(outcome.transfers[0].carried)
        self.assertEqual(outcome.status, "unsettled")

    def test_the_earlier_transfer_is_carried_not_paid_and_names_where_it_went(self):
        second = self.club.play({"Ana": 0, "Ben": 0})
        self.club.close(second, self.old)
        outcome = queries.night_outcome(self.club.host.group.nights.get(pk=self.first))
        transfer = outcome.transfers[0]
        self.assertIsNone(transfer.paid)
        self.assertEqual(transfer.carried.plan.night_id, second)
        self.assertEqual((outcome.status, outcome.paid_count, outcome.carried_count, outcome.still_to_pay), ("settled", 0, 1, 0))
        self.assertEqual(outcome.part_for(self.club.members["Ana"].pk).kind, "settled")
        later = queries.night_outcome(self.club.host.group.nights.get(pk=second))
        self.assertEqual([c.transfer_id for c in later.carried_in], [transfer.pk])
        balance, parts, total = later.makeup_for(self.club.members["Ana"].pk)
        self.assertEqual((balance, [amount for _, amount in parts], total), (0, [-50000], -50000))
        self.assertIsNone(later.makeup_for(self.club.members["Carlo"].pk))
        self.assertEqual(queries.unpaid_in(self.club.host.group.nights.get(pk=self.first)), [])

    def test_both_sessions_logs_say_it(self):
        second = self.club.play({"Ana": 0, "Ben": 0})
        self.club.close(second, self.old)
        self.assertTrue(AuditEvent.objects.filter(action="transfer.carried", summary__startswith="Carried into the session of").exists())
        self.assertIn("1 earlier transfer carried in", AuditEvent.objects.filter(action="night.closed").latest("pk").summary)

    def test_a_carried_transfer_cannot_be_marked_paid(self):
        second = self.club.play({"Ana": 0, "Ben": 0})
        self.club.close(second, self.old)
        with self.assertRaisesMessage(RuleError, "Mark it paid there."):
            services.mark_paid(self.first, self.club.host, self.old[0].pk, uuid.uuid4())

    def test_reopening_the_later_session_makes_the_transfer_unpaid_again(self):
        before = self.club.owed()
        second = self.club.play({"Ana": 0, "Ben": 0})
        self.club.close(second, self.old)
        services.reopen_night(second, self.club.host, "wrong count")
        self.assertEqual(self.club.owed(), before)
        self.assertEqual(queries.settle_states([self.first])[self.first].status, "unsettled")
        self.assertEqual(CarriedTransfer.objects.count(), 1)  # kept; its list is no longer current
        services.mark_paid(self.first, self.club.host, self.old[0].pk, uuid.uuid4())
        self.assertEqual(queries.carryable(self.club.host.group.nights.get(pk=second)), [])
        self.club.close(second)
        self.assertEqual(self.club.transfers(second), {})

    def test_the_earlier_session_cannot_be_reopened_while_its_transfer_is_carried(self):
        second = self.club.play({"Ana": 0, "Ben": 0})
        self.club.close(second, self.old)
        with self.assertRaisesMessage(RuleError, "Reopen that session first."):
            services.reopen_night(self.first, self.club.host, "typo")
        services.reopen_night(second, self.club.host, "undo")
        services.reopen_night(self.first, self.club.host, "typo")

    def test_a_chain_over_three_sessions(self):
        second = self.club.play({"Ana": -100, "Ben": 100})
        self.club.close(second, self.old)
        third = self.club.play({"Ana": 600, "Ben": -600})
        self.assertEqual([t.plan.night_id for t in queries.carryable(self.club.host.group.nights.get(pk=third))], [second])
        self.club.close(third, self.club.unpaid(second))
        self.assertEqual(self.club.transfers(third), {})
        self.assertEqual(self.club.owed(), {"Ana": 0, "Ben": 0, "Carlo": 0, "Dee": 0})
        with self.assertRaisesMessage(RuleError, "Reopen that session first."):
            services.reopen_night(second, self.club.host, "no")

    def test_a_repeated_close_writes_nothing_twice(self):
        second = self.club.play({"Ana": 0, "Ben": 0})
        first = self.club.close(second, self.old)
        self.assertEqual(self.club.close(second, self.old).pk, first.pk)
        self.assertEqual((SettlementPlan.objects.filter(night_id=second).count(), CarriedTransfer.objects.count()), (1, 1))

    @override_settings(CARRY_DEBTS=False)
    def test_the_switch_carries_nothing(self):
        second = self.club.play({"Ana": 500, "Ben": -500})
        self.club.close(second, self.old)
        self.assertEqual(self.club.transfers(second), {("Ben", "Ana"): 500})
        self.assertEqual(CarriedTransfer.objects.count(), 0)


class WhatQualifiesTests(TestCase):
    def setUp(self):
        self.club = Club("Ana", "Ben", "Carlo")
        self.first = self.club.closed({"Ana": -500, "Ben": 500})
        self.old = self.club.unpaid(self.first)

    def night(self, night_id):
        return self.club.host.group.nights.get(pk=night_id)

    def refused(self, night_id, transfers):
        with self.assertRaisesMessage(RuleError, "Nothing was closed."):
            self.club.close(night_id, transfers)
        self.assertFalse(self.night(night_id).is_closed)
        self.assertFalse(SettlementPlan.objects.filter(night_id=night_id).exists())

    def test_paid(self):
        second = self.club.play({"Ana": 0, "Ben": 0})
        services.mark_paid(self.first, self.club.host, self.old[0].pk, uuid.uuid4())
        self.assertEqual(queries.carryable(self.night(second)), [])
        self.refused(second, self.old)

    def test_carried_already(self):
        second = self.club.play({"Ana": 0, "Ben": 0})
        third = self.club.play({"Ana": 0, "Ben": 0})
        self.club.close(second, self.old)
        self.assertEqual([t.plan.night_id for t in queries.carryable(self.night(third))], [second] if self.club.unpaid(second) else [])
        self.refused(third, self.old)

    def test_one_of_the_two_did_not_play_tonight(self):
        second = self.club.play({"Ana": -100, "Carlo": 100})
        self.assertEqual(queries.carryable(self.night(second)), [])
        self.refused(second, self.old)

    def test_another_unit(self):
        second = self.club.play({"Ana": 0, "Ben": 0}, unit="chips")
        self.assertEqual(queries.carryable(self.night(second)), [])
        self.refused(second, self.old)

    def test_an_archived_session(self):
        second = self.club.play({"Ana": 0, "Ben": 0})
        games.archive_night(self.first, self.club.host)
        self.assertEqual(queries.carryable(self.night(second)), [])
        self.refused(second, self.old)

    def test_a_retired_list(self):
        second = self.club.play({"Ana": 0, "Ben": 0})
        services.reopen_night(self.first, self.club.host, "again")
        self.refused(second, self.old)

    def test_another_group(self):
        other = Club("Ana", "Ben")
        elsewhere = other.closed({"Ana": -100, "Ben": 100})
        second = self.club.play({"Ana": 0, "Ben": 0})
        self.refused(second, other.unpaid(elsewhere))

    def test_its_own_transfers_and_nonsense(self):
        second = self.club.play({"Ana": 0, "Ben": 0})
        with self.assertRaisesMessage(RuleError, "Choose the earlier transfers from the list."):
            services.close_night(second, self.club.host, ["x"])
        with self.assertRaisesMessage(RuleError, "Nothing was closed."):
            services.close_night(second, self.club.host, [999999])

    def test_one_bad_transfer_refuses_the_whole_close(self):
        other = self.club.closed({"Ana": -100, "Ben": 100})
        second = self.club.play({"Ana": 0, "Ben": 0})
        services.mark_paid(other, self.club.host, self.club.unpaid(other)[0].pk, uuid.uuid4())
        self.refused(second, self.old + self.club.unpaid(other))
        self.assertEqual(CarriedTransfer.objects.count(), 0)
