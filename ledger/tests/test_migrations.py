"""The one-time conversion of chip counts to amounts (ledger 0005)."""

import datetime
import uuid

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

BEFORE = [
    ("games", "0002_gamesession_participant_settingsversion_and_more"),
    ("ledger", "0004_finalization_playerresult_and_more"),
    ("settlement", "0002_payment_paymentreversal_payment_payment_session_and_more"),
]
AFTER = [
    ("games", "0004_alter_gamesession_state_and_more"),
    ("ledger", "0006_balanceadjustment_adjustment_not_zero_and_more"),
    ("settlement", "0004_payment_payment_amount_positive_and_more"),
]


class ChipsToAmountsMigrationTests(TransactionTestCase):
    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return MigrationExecutor(connection).loader.project_state(targets).apps

    def tearDown(self):
        MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def make_session(self, apps, name, *, rate, state, buy_ins, cash_outs, adjustments=(), results=None):
        """Old-schema rows. ``buy_ins`` are centavos; ``cash_outs`` and ``adjustments`` are chips."""
        User = apps.get_model("accounts", "User")
        Group = apps.get_model("groups", "GameGroup")
        Member = apps.get_model("groups", "Member")
        Table = apps.get_model("games", "Table")
        Session = apps.get_model("games", "GameSession")
        Version = apps.get_model("games", "SettingsVersion")
        Participant = apps.get_model("games", "Participant")
        user = User.objects.create(username=f"host-{name}")
        group = Group.objects.create(name=name, created_by=user)
        table = Table.objects.create(group=group, name="T", seat_count=9)
        session = Session.objects.create(
            group=group, table=table, game_date=datetime.date(2026, 10, 3), state=state, seat_count=9,
            rate_centavos=rate[0], rate_chips=rate[1], created_by=user,
        )
        version = Version.objects.create(
            session=session, number=1, small_blind_centavos=1000, big_blind_centavos=2000,
            min_buy_in_centavos=50000, max_buy_in_centavos=200000, default_buy_in_centavos=100000,
            chips_per_buy_in=100000 * rate[1] // rate[0], created_by=user,
        )
        participants = []
        for order, (amount, chips) in enumerate(zip(buy_ins, cash_outs), start=1):
            member = Member.objects.create(group=group, display_name=f"P{order}")
            participant = Participant.objects.create(session=session, member=member, join_order=order, added_by=user)
            participants.append(participant)
            apps.get_model("ledger", "BuyIn").objects.create(
                session=session, participant=participant, settings_version=version, amount_centavos=amount,
                chips=amount * rate[1] // rate[0], request_id=uuid.uuid4(), recorded_by=user,
            )
            for part in chips if isinstance(chips, tuple) else (chips,):
                apps.get_model("ledger", "CashOut").objects.create(
                    session=session, participant=participant, chips=part, request_id=uuid.uuid4(), recorded_by=user
                )
        for index, delta in adjustments:
            apps.get_model("ledger", "BalanceAdjustment").objects.create(
                session=session, participant=participants[index], chips_delta=delta, mode="player", note="n",
                request_id=uuid.uuid4(), recorded_by=user,
            )
        if results:
            total = sum(buy_ins)
            finalization = apps.get_model("ledger", "Finalization").objects.create(
                session=session, revision=1, total_buy_in_centavos=total, total_cash_out_centavos=total,
                chips_issued=total * rate[1] // rate[0], rate_centavos=rate[0], rate_chips=rate[1],
                settings_snapshot=[{"number": 1, "default_buy_in_centavos": 100000, "chips_per_buy_in": 10000}],
                finalized_by=user,
            )
            for participant, amount, (cash_out, adjustment_chips) in zip(participants, buy_ins, results):
                apps.get_model("ledger", "PlayerResult").objects.create(
                    finalization=finalization, participant=participant, member_id=participant.member_id,
                    group=group, game_date=session.game_date, buy_in_total_centavos=amount, buy_in_count=1,
                    chips_cashed=0, adjustment_chips=adjustment_chips, cash_out_centavos=cash_out,
                    net_centavos=cash_out - amount,
                )
        return session.pk

    def test_chip_counts_become_amounts_and_the_books_still_balance(self):
        old = self.migrate(BEFORE)
        # ₱1,000 = 10,000 chips. Finalized with an override of −500 chips on the first player.
        whole = self.make_session(
            old, "whole", rate=(10, 1), state="finalized", buy_ins=[100000, 100000, 50000],
            cash_outs=[(10000, 6000), 7000, 2500], adjustments=[(0, -500)],
            results=[(155000, -500), (70000, 0), (25000, 0)],
        )
        # ₱1,000 = 30,000 chips: a chip is worth a third of a centavo more than 3. Finalized.
        fractional = self.make_session(
            old, "fractional", rate=(10, 3), state="finalized", buy_ins=[100000, 100000, 100000],
            cash_outs=[(40000, 1), 29999, 20000], results=[(133337, 0), (99997, 0), (66666, 0)],
        )
        # ₱1,000 = 20 chips, still running, one player cashed out so far.
        running = self.make_session(
            old, "running", rate=(5000, 1), state="running", buy_ins=[100000, 200000], cash_outs=[(), 55],
        )

        new = self.migrate(AFTER)
        CashOut = new.get_model("ledger", "CashOut")
        Result = new.get_model("ledger", "PlayerResult")
        Finalization = new.get_model("ledger", "Finalization")
        Adjustment = new.get_model("ledger", "BalanceAdjustment")

        def amounts(session_id):
            return list(CashOut.objects.filter(session_id=session_id).order_by("id").values_list("amount", flat=True))

        self.assertEqual(amounts(whole), [100000, 60000, 70000, 25000])
        self.assertEqual(Adjustment.objects.get(session_id=whole).amount, -5000)
        results = list(Result.objects.filter(finalization__session_id=whole).order_by("id"))
        self.assertEqual([(r.cashed_out, r.adjustment, r.cash_out, r.net, r.unit) for r in results], [
            (160000, -5000, 155000, 55000, "php"), (70000, 0, 70000, -30000, "php"), (25000, 0, 25000, -25000, "php"),
        ])
        finalization = Finalization.objects.get(session_id=whole)
        self.assertEqual((finalization.raw_difference, finalization.total_buy_in, finalization.unit), (5000, 250000, "php"))
        self.assertEqual(finalization.settings_snapshot, [{"number": 1, "default_buy_in": 100000}])

        # Fractional rate: each player's rows add up to the frozen result, and the game still balances.
        self.assertEqual(amounts(fractional), [133334, 3, 99997, 66666])
        self.assertEqual(sum(amounts(fractional)), 300000)
        self.assertEqual(
            [r.cashed_out for r in Result.objects.filter(finalization__session_id=fractional).order_by("id")],
            [133337, 99997, 66666],
        )

        self.assertEqual(amounts(running), [275000])  # 55 chips at ₱50
        Session = new.get_model("games", "GameSession")
        self.assertEqual(set(Session.objects.values_list("unit", flat=True)), {"php"})
        self.assertFalse(hasattr(Session, "rate_centavos"))
