"""Races between simultaneous requests. These run on SQLite and must also pass on PostgreSQL:

    DATABASE_URL=postgres://localhost:5432/pokernights manage.py test web.tests.test_concurrency
"""

import threading
import uuid

from django.db import connection
from django.test import TransactionTestCase

from games import services as games
from games.models import Participant, ParticipantBatch
from games.tests.test_add_players import Roster
from groups.errors import RuleError
from groups.tests.helpers import add_player
from ledger import queries as ledger_queries
from ledger import services as ledger
from ledger.models import BuyIn, CashOut, Finalization, PlayerResult
from ledger.tests.helpers import Night
from ledger.tests.test_balance import worked_example
from settlement import services as settlement
from settlement.models import Payment, SettlementPlan, Transfer


def race(*actions):
    """Run the actions at the same moment, one thread each. Returns one outcome per action:
    ``("ok", value)``, ``("refused", message)`` for a RuleError, or ``("error", text)``."""
    barrier = threading.Barrier(len(actions))
    outcomes = [None] * len(actions)

    def run(index, action):
        try:
            barrier.wait(timeout=10)
            outcomes[index] = ("ok", action())
        except RuleError as error:
            outcomes[index] = ("refused", str(error))
        except Exception as error:  # noqa: BLE001 - a test must report any crash, not hide it
            outcomes[index] = ("error", repr(error))
        finally:
            connection.close()

    threads = [threading.Thread(target=run, args=(i, action)) for i, action in enumerate(actions)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    return outcomes


def kinds(outcomes):
    return sorted(kind for kind, _ in outcomes)


class ConcurrentJoinTests(TransactionTestCase):
    def test_ten_players_race_for_the_last_seat(self):
        night = Night("Seated", state="open", seat_count=2)
        members = [add_player(night.group, f"p{i}") for i in range(10)]
        outcomes = race(*[
            (lambda member=member: games.add_participant(night.session.pk, member, member.pk)) for member in members
        ])
        self.assertEqual(kinds(outcomes), ["ok"] + ["refused"] * 9, outcomes)
        self.assertTrue(all("full" in message for kind, message in outcomes if kind == "refused"))
        self.assertEqual(night.session.participants.filter(status=Participant.Status.JOINED).count(), 2)
        self.assertEqual(sorted(night.session.participants.values_list("join_order", flat=True)), [1, 2])

    def test_one_player_taps_join_ten_times(self):
        night = Night(state="open")
        member = add_player(night.group, "ben")
        outcomes = race(*[lambda: games.add_participant(night.session.pk, member, member.pk)] * 10)
        self.assertEqual(kinds(outcomes), ["ok"] * 10, outcomes)
        self.assertEqual(len({participant.pk for _, participant in outcomes}), 1)
        self.assertEqual(Participant.objects.filter(session=night.session).count(), 1)


class ConcurrentBuyInTests(TransactionTestCase):
    def test_one_request_id_from_ten_threads_records_once(self):
        night = Night("A")
        request_id = uuid.uuid4()
        outcomes = race(*[lambda: night.buy("A", 1000, request_id)] * 10)
        self.assertEqual(kinds(outcomes), ["ok"] * 10, outcomes)
        self.assertEqual(len({buy_in.pk for _, buy_in in outcomes}), 1)
        self.assertEqual(BuyIn.objects.count(), 1)
        self.assertEqual(ledger_queries.summary(night.session).total, 100000)

    def test_ten_different_buy_ins_at_once_are_all_counted(self):
        night = Night("A", "B")
        before = night.refresh().version
        outcomes = race(*[(lambda name=name: night.buy(name, 1000)) for name in "AB" * 5])
        self.assertEqual(kinds(outcomes), ["ok"] * 10, outcomes)
        summary = ledger_queries.summary(night.session)
        self.assertEqual((summary.buy_in_count, summary.total), (10, 1000000))
        session = night.refresh()
        self.assertEqual(session.version, before + 10)  # no update was lost

    def test_buy_in_races_with_the_end_of_play(self):
        night = Night("A")
        outcomes = race(
            lambda: night.buy("A", 1000),
            lambda: games.transition(night.session.pk, night.host, "end"),
        )
        self.assertEqual(outcomes[1][0], "ok", outcomes)
        # Either the buy-in landed before play ended, or it was refused. Never a half state.
        self.assertIn(outcomes[0][0], ("ok", "refused"), outcomes)
        self.assertEqual(BuyIn.objects.count(), 1 if outcomes[0][0] == "ok" else 0)
        self.assertEqual(night.refresh().state, "reconciliation")


class ConcurrentFinalizeTests(TransactionTestCase):
    def test_two_finalizes_write_one_set_of_results(self):
        night = worked_example()
        outcomes = race(*[lambda: settlement.finalize(night.session.pk, night.host)] * 4)
        self.assertEqual(kinds(outcomes), ["ok"] * 4, outcomes)
        self.assertEqual((Finalization.objects.count(), PlayerResult.objects.count()), (1, 3))

    def test_two_hosts_close_the_session_at_once(self):
        night = worked_example()
        settlement.finalize(night.session.pk, night.host)
        outcomes = race(*[lambda: settlement.close_night(night.session.night_id, night.host)] * 4)
        self.assertEqual(kinds(outcomes), ["ok"] * 4, outcomes)
        self.assertEqual((SettlementPlan.objects.count(), Transfer.objects.count()), (1, 2))

    def test_two_hosts_start_the_next_set_at_once(self):
        night = worked_example()
        outcomes = race(*[lambda: games.start_next_set(night.session.night_id, night.host)] * 4)
        self.assertEqual(kinds(outcomes), ["ok"] + ["refused"] * 3, outcomes)
        self.assertEqual(sorted(night.session.night.sets.values_list("set_number", flat=True)), [1, 2])

    def test_close_races_with_the_next_set(self):
        night = worked_example()
        settlement.finalize(night.session.pk, night.host)
        outcomes = race(
            lambda: settlement.close_night(night.session.night_id, night.host),
            lambda: games.start_next_set(night.session.night_id, night.host),
        )
        self.assertEqual(kinds(outcomes), ["ok", "refused"], outcomes)
        night.session.night.refresh_from_db()
        sets = night.session.night.sets.count()
        # Either the session closed with one set, or a second set opened and it stayed open.
        self.assertIn((night.session.night.status, sets), (("closed", 1), ("open", 2)))

    def test_finalize_races_with_a_money_write(self):
        """A cash-out that would unbalance the books arrives while the host finalizes."""
        for _ in range(5):
            night = worked_example()
            outcomes = race(
                lambda: settlement.finalize(night.session.pk, night.host),
                lambda: night.cash("C", 50),
            )
            self.assertNotIn("error", kinds(outcomes), outcomes)
            session = night.refresh()
            if session.state == "finalized":
                # Finalize won: the late cash-out was refused and the snapshot balances.
                self.assertEqual(kinds(outcomes), ["ok", "refused"], outcomes)
                self.assertEqual(CashOut.objects.filter(session=session).count(), 3)
                finalization = Finalization.objects.get(session=session)
                self.assertEqual(finalization.total_cash_out, finalization.total_buy_in)
                self.assertEqual(sum(finalization.results.values_list("net", flat=True)), 0)
            else:
                # The cash-out won: the books no longer balance, so finalize was refused.
                self.assertEqual(kinds(outcomes), ["ok", "refused"], outcomes)
                self.assertEqual(session.state, "reconciliation")
                self.assertFalse(Finalization.objects.filter(session=session).exists())
                self.assertEqual(ledger_queries.balance(session).difference, 5000)

    def test_reversal_races_with_finalize(self):
        night = worked_example()
        buy_in = BuyIn.objects.filter(session=night.session).first()
        outcomes = race(
            lambda: settlement.finalize(night.session.pk, night.host),
            lambda: ledger.reverse_buy_in(night.session.pk, night.host, buy_in.pk, "late correction"),
        )
        self.assertEqual(kinds(outcomes), ["ok", "refused"], outcomes)
        finalized = night.refresh().state == "finalized"
        self.assertEqual(Finalization.objects.count(), 1 if finalized else 0)
        if finalized:
            self.assertEqual(sum(PlayerResult.objects.values_list("net", flat=True)), 0)


class ConcurrentPaidMarkTests(TransactionTestCase):
    def test_two_hosts_mark_one_transfer_paid_at_once(self):
        night = worked_example()
        settlement.finalize(night.session.pk, night.host)
        settlement.close_night(night.session.night_id, night.host)
        transfer = Transfer.objects.order_by("position").first()
        outcomes = race(*[
            (lambda: settlement.mark_paid(night.session.night_id, night.host, transfer.pk, uuid.uuid4())) for _ in range(6)
        ])
        self.assertEqual(kinds(outcomes), ["ok"] * 6, outcomes)
        self.assertEqual(Payment.objects.filter(transfer=transfer, active=True).count(), 1)
        self.assertEqual(Payment.objects.count(), 1)


class ConcurrentBatchAddTests(TransactionTestCase):
    def test_two_hosts_submit_overlapping_selections_at_once(self):
        roster = Roster()
        outcomes = race(
            lambda: roster.add("Ana", "Ben", "Carlo"),
            lambda: roster.add("Carlo", "Dani"),
        )
        self.assertEqual(kinds(outcomes), ["ok", "refused"], outcomes)
        refused = next(message for kind, message in outcomes if kind == "refused")
        self.assertIn("Carlo is already at the table. Nothing was added.", refused)
        # Whichever request won, its whole selection is in and the other's is entirely out.
        self.assertIn(roster.at_table(), (["Ana", "Ben", "Carlo"], ["Carlo", "Dani"]))
        self.assertEqual(ParticipantBatch.objects.count(), 1)

    def test_two_batches_race_for_the_last_seats(self):
        roster = Roster(seat_count=3)
        outcomes = race(lambda: roster.add("Ana", "Ben"), lambda: roster.add("Carlo", "Dani"))
        self.assertEqual(kinds(outcomes), ["ok", "refused"], outcomes)
        self.assertIn("Only 1 seat is free and you selected 2 players", next(m for k, m in outcomes if k == "refused"))
        self.assertIn(roster.at_table(), (["Ana", "Ben"], ["Carlo", "Dani"]))

    def test_a_batch_races_with_single_joins(self):
        roster = Roster(seat_count=4)
        ana = roster.members["Ana"]
        outcomes = race(
            lambda: roster.add("Ana", "Ben", "Carlo", "Dani"),
            lambda: games.add_participant(roster.session.pk, ana, ana.pk),
        )
        self.assertNotIn("error", kinds(outcomes), outcomes)
        # Either the batch added all four (and the self-join found Ana already in), or the
        # self-join came first and the batch added nobody.
        self.assertIn(roster.at_table(), (["Ana", "Ben", "Carlo", "Dani"], ["Ana"]))
        self.assertEqual(len(set(roster.session.participants.values_list("join_order", flat=True))), len(roster.at_table()))

    def test_one_request_sent_six_times_adds_one_batch(self):
        roster = Roster()
        request_id = uuid.uuid4()
        outcomes = race(*[lambda: roster.add(request_id=request_id)] * 6)
        self.assertEqual(kinds(outcomes), ["ok"] * 6, outcomes)
        self.assertEqual((ParticipantBatch.objects.count(), Participant.objects.count()), (1, 4))
        self.assertEqual(len({tuple(p.pk for p in added) for _, added in outcomes}), 1)
