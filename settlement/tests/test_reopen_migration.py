"""Settlement 0007: a session may hold several plans, one of them current. Plans written before it stay current."""

import datetime

from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

BEFORE = ("settlement", "0006_payment_payment_night_payment_payment_request_once_and_more")
AFTER = ("settlement", "0007_reopening")


class PlanPerSessionMigrationTests(TransactionTestCase):
    def migrate(self, target):
        executor = MigrationExecutor(connection)
        targets = [node for node in executor.loader.graph.leaf_nodes() if node[0] != "settlement"] + [target]
        executor.migrate(targets)
        return MigrationExecutor(connection).loader.project_state(targets).apps

    def tearDown(self):
        MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())

    def test_existing_plans_stay_current_and_a_second_plan_is_allowed(self):
        apps = self.migrate(BEFORE)
        user = apps.get_model("accounts", "User").objects.create(username="host")
        group = apps.get_model("groups", "GameGroup").objects.create(name="G", created_by=user)
        table = apps.get_model("games", "Table").objects.create(group=group, name="T", seat_count=9)
        night = apps.get_model("games", "GameNight").objects.create(
            group=group, table=table, game_date=datetime.date(2026, 10, 3), status="closed", created_by=user,
        )
        payer, payee = (apps.get_model("groups", "Member").objects.create(group=group, display_name=n) for n in "AB")
        plan = apps.get_model("settlement", "SettlementPlan").objects.create(night=night)
        apps.get_model("settlement", "Transfer").objects.create(plan=plan, position=1, payer=payer, payee=payee, amount=500)

        apps = self.migrate(AFTER)
        Plan = apps.get_model("settlement", "SettlementPlan")
        kept = Plan.objects.get(pk=plan.pk)
        self.assertTrue(kept.is_current)
        self.assertEqual((kept.voided_at, kept.void_reason, kept.transfers.count()), (None, "", 1))
        with self.assertRaises(IntegrityError), transaction.atomic():
            Plan.objects.create(night_id=night.pk)  # two current plans
        Plan.objects.filter(pk=kept.pk).update(is_current=False)
        Plan.objects.create(night_id=night.pk)
        self.assertEqual(Plan.objects.filter(night_id=night.pk).count(), 2)
