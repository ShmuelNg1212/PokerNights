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
from games.models import PlayInterval, PlayPeriod
from ledger.models import BuyIn, CashOut, CashOutBatch, Finalization, PlayerResult
from ledger.tests.test_batch import ready_ids, six_players
from ledger.tests.test_counts import count
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


class ConcurrentEndOfSetTests(TransactionTestCase):
    def test_two_hosts_confirm_the_same_review_at_once(self):
        night = six_players()
        reviewed = ready_ids(night)
        outcomes = race(*[
            (lambda: ledger.cash_out_counted(night.session.pk, night.host, reviewed, uuid.uuid4())) for _ in range(4)
        ])
        self.assertEqual(kinds(outcomes), ["ok"] + ["refused"] * 3, outcomes)
        self.assertEqual((CashOutBatch.objects.count(), CashOut.objects.count()), (1, 4))
        self.assertEqual(CashOut.objects.values("participant").distinct().count(), 4)

    def test_one_confirmation_sent_six_times_records_once(self):
        night = six_players()
        reviewed, request_id = ready_ids(night), uuid.uuid4()
        outcomes = race(*[lambda: ledger.cash_out_counted(night.session.pk, night.host, reviewed, request_id)] * 6)
        self.assertEqual(kinds(outcomes), ["ok"] * 6, outcomes)
        self.assertEqual((CashOutBatch.objects.count(), CashOut.objects.count()), (1, 4))

    def test_batch_races_with_an_individual_cash_out(self):
        for _ in range(4):
            night = six_players()
            reviewed = ready_ids(night)
            outcomes = race(
                lambda: ledger.cash_out_counted(night.session.pk, night.host, reviewed, uuid.uuid4()),
                lambda: night.cash("A", 2500),
            )
            self.assertEqual(kinds(outcomes), ["ok", "refused"], outcomes)
            # A has exactly one final cash-out, whichever request won. The batch is whole or absent.
            self.assertEqual(CashOut.objects.filter(participant=night.players["A"]).count(), 1)
            self.assertIn(CashOut.objects.filter(session=night.session).count(), (1, 4))

    def test_batch_races_with_a_count_change(self):
        for _ in range(4):
            night = six_players()
            reviewed = ready_ids(night)
            outcomes = race(
                lambda: ledger.cash_out_counted(night.session.pk, night.host, reviewed, uuid.uuid4()),
                lambda: count(night, "B", 1400),
            )
            self.assertEqual(kinds(outcomes), ["ok", "refused"], outcomes)
            cash_outs = CashOut.objects.filter(session=night.session)
            if outcomes[0][0] == "ok":
                # The batch used the reviewed count; the later change was refused.
                self.assertEqual(cash_outs.get(participant=night.players["B"]).amount, 150000)
            else:
                self.assertEqual(cash_outs.count(), 0)  # the stale batch recorded nothing
                self.assertEqual(night.line("B").count.amount, 140000)

    def test_end_of_play_sent_twice_stops_the_timers_once(self):
        night = Night("A", "B", "C")
        outcomes = race(*[lambda: games.transition(night.session.pk, night.host, "end")] * 3)
        self.assertEqual(kinds(outcomes), ["ok"] + ["refused"] * 2, outcomes)
        session = night.refresh()
        self.assertEqual(set(PlayInterval.objects.values_list("ended_at", flat=True)), {session.ended_at})
        self.assertEqual((PlayPeriod.objects.count(), PlayInterval.objects.count()), (1, 3))


class ConcurrentRakeTests(TransactionTestCase):
    def setUp(self):
        if connection.vendor != 'postgresql':
            self.skipTest('Rake serialization requires PostgreSQL row locks.')
        from ledger.tests.test_rake import configure
        self.n = Night('A', 'B', state='open')
        configure(self.n, rake_mode='percent', rake_basis_points=500)

    def test_opening_retries_have_one_fee_per_player(self):
        from ledger.models import RakeEntry
        request = uuid.uuid4()
        outcomes = race(*[lambda: games.transition(self.n.session.pk, self.n.host, 'start', request_id=request)] * 4)
        self.assertEqual(kinds(outcomes), ['ok'] * 4, outcomes)
        self.assertEqual(RakeEntry.objects.count(), 2)
        self.assertEqual(ledger_queries.group_rake(self.n.group)[0]['php'], 10000)

    def test_configuration_racing_buy_in_never_rewrites_fee(self):
        data = {**games.current_settings(self.n.session).stakes(), 'rake_mode': 'percent', 'rake_basis_points': 1000}
        outcomes = race(lambda: self.n.buy('A', 1000),
                        lambda: games.update_settings(self.n.session.pk, self.n.host, data, request_id=uuid.uuid4()))
        self.assertEqual(outcomes[0][0], 'ok', outcomes)
        self.assertIn(outcomes[1][0], ('ok', 'refused'), outcomes)
        buy = BuyIn.objects.get()
        self.assertEqual(buy.rake_amount, 10000 if outcomes[1][0] == 'ok' else 5000)
        self.assertEqual(buy.settings_version.rake_basis_points, 1000 if outcomes[1][0] == 'ok' else 500)

    def test_simultaneous_buy_ins_have_exact_fees_and_versions(self):
        from ledger.models import RakeEntry
        before = self.n.refresh().version
        outcomes = race(*[lambda: self.n.buy('A', 1000)] * 5)
        self.assertEqual(kinds(outcomes), ['ok'] * 5, outcomes)
        self.assertEqual(RakeEntry.objects.count(), 5)
        self.assertEqual(ledger_queries.group_rake(self.n.group)[0]['php'], 25000)
        self.assertEqual(self.n.refresh().version, before + 5)

    def test_reversal_racing_rebuy_excludes_only_reversed_fee(self):
        b = self.n.buy('A', 1000)
        outcomes = race(lambda: ledger.reverse_buy_in(self.n.session.pk, self.n.host, b.pk, 'duplicate'),
                        lambda: self.n.buy('A', 1000))
        self.assertEqual(kinds(outcomes), ['ok', 'ok'], outcomes)
        self.assertEqual(ledger_queries.group_rake(self.n.group)[0]['php'], 5000)


class ConcurrentArchiveTests(TransactionTestCase):
    def closed(self):
        night = worked_example()
        settlement.finalize(night.session.pk, night.host)
        settlement.close_night(night.session.night_id, night.host)
        return night

    def test_two_hosts_archive_at_once(self):
        from audit.models import AuditEvent
        night = self.closed()
        outcomes = race(*[lambda: games.archive_night(night.session.night_id, night.host)] * 2)
        self.assertEqual(kinds(outcomes), ["ok", "ok"], outcomes)
        self.assertEqual(AuditEvent.objects.filter(action="night.archived").count(), 1)

    def test_archive_races_with_a_paid_mark(self):
        night = self.closed()
        night_id = night.session.night_id
        transfer = Transfer.objects.order_by("position").first()
        outcomes = race(
            lambda: settlement.mark_paid(night_id, night.host, transfer.pk, uuid.uuid4()),
            lambda: games.archive_night(night_id, night.host),
        )
        self.assertEqual(outcomes[1][0], "ok", outcomes)
        # Either the payment landed before the archive, or it was refused. Never a write after it.
        self.assertIn(outcomes[0][0], ("ok", "refused"), outcomes)
        self.assertEqual(Payment.objects.count(), 1 if outcomes[0][0] == "ok" else 0)

    def test_delete_races_with_a_new_set(self):
        from games.models import GameNight, GameSession
        night = Night("A")
        games.transition(night.session.pk, night.host, "cancel", "nobody came")
        night_id = night.session.night_id
        outcomes = race(
            lambda: games.start_next_set(night_id, night.host),
            lambda: games.delete_night(night_id, night.host),
        )
        self.assertNotIn("error", kinds(outcomes), outcomes)
        # Either the session is gone with every set, or the new set kept it alive.
        if GameNight.objects.filter(pk=night_id).exists():
            self.assertEqual(GameSession.objects.filter(night_id=night_id).count(), 2)
        else:
            self.assertEqual(GameSession.objects.filter(night_id=night_id).count(), 0)


class ConcurrentGroupArchiveTests(TransactionTestCase):
    def test_archive_races_with_a_new_session(self):
        from games.models import GameNight
        from games.tests.helpers import make_session, make_table
        from groups import services as groups
        from groups.models import GameGroup
        from groups.tests.helpers import make_group
        group, host = make_group()
        table = make_table(host)
        outcomes = race(
            lambda: make_session(host, table=table),
            lambda: groups.archive_group(host),
        )
        self.assertNotIn("error", kinds(outcomes), outcomes)
        # Exactly one wins: an archived group never gains a session, and a group with a draft set is not archived.
        self.assertEqual(kinds(outcomes), ["ok", "refused"], outcomes)
        archived = GameGroup.objects.get(pk=group.pk).is_archived
        self.assertEqual(GameNight.objects.filter(group=group).count(), 0 if archived else 1)


class ConcurrentInviteSignupTests(TransactionTestCase):
    def test_two_sign_ups_race_for_the_last_use_of_an_invite(self):
        from django.contrib.auth import get_user_model
        from django.test import Client
        from django.urls import reverse
        from groups import services as groups
        from groups.models import Invite, Member
        from groups.tests.helpers import make_group

        group, host = make_group()
        invite, token = groups.create_invite(host)
        Invite.objects.filter(pk=invite.pk).update(max_uses=1)
        url = reverse("invite_accept", args=[token])

        def sign_up(name):
            data = {"username": name, "password1": "tablestakes-91", "password2": "tablestakes-91", "next": url}
            return lambda: Client().post(reverse("signup"), data).status_code

        outcomes = race(sign_up("first"), sign_up("second"))
        self.assertNotIn("error", kinds(outcomes), outcomes)
        # Both accounts exist; the invite admits exactly one of them and is never used past its limit.
        self.assertEqual(get_user_model().objects.filter(username__in=["first", "second"]).count(), 2)
        self.assertEqual(Member.objects.filter(group=group, user__username__in=["first", "second"]).count(), 1)
        self.assertEqual(Invite.objects.get(pk=invite.pk).use_count, 1)
