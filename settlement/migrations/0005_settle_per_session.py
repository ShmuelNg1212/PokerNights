"""Move settle-up from a set to its session, and name members instead of participants.

Until now each game had its own transfer list. A session can have several
sets, and it settles once. Every existing game is a session with one set, so
each existing plan, transfer and payment keeps its amount and moves across
unchanged.
"""

import django.db.models.deletion
from django.db import migrations, models


def move_to_sessions(apps, schema_editor):
    Plan = apps.get_model("settlement", "SettlementPlan")
    Transfer = apps.get_model("settlement", "Transfer")
    Payment = apps.get_model("settlement", "Payment")
    for plan in Plan.objects.select_related("finalization__session"):
        plan.night_id = plan.finalization.session.night_id
        plan.save(update_fields=["night"])
    for transfer in Transfer.objects.select_related("payer", "payee"):
        transfer.payer_member_id = transfer.payer.member_id
        transfer.payee_member_id = transfer.payee.member_id
        transfer.save(update_fields=["payer_member", "payee_member"])
    for payment in Payment.objects.select_related("session", "payer", "payee"):
        payment.night_id = payment.session.night_id
        payment.payer_member_id = payment.payer.member_id if payment.payer_id else None
        payment.payee_member_id = payment.payee.member_id if payment.payee_id else None
        payment.save(update_fields=["night", "payer_member", "payee_member"])


def member_fk(related_name, null):
    return models.ForeignKey(
        null=null, blank=null, on_delete=django.db.models.deletion.PROTECT, related_name=related_name, to="groups.member"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("settlement", "0004_payment_payment_amount_positive_and_more"),
        ("games", "0007_gamenight_night_group_status_date_and_more"),
        ("groups", "0002_invite"),
        ("ledger", "0006_balanceadjustment_adjustment_not_zero_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(model_name="transfer", name="transfer_payer_is_not_payee"),
        migrations.RemoveConstraint(model_name="payment", name="payment_request_once"),
        migrations.RemoveIndex(model_name="payment", name="payment_session"),
        migrations.AddField(
            "settlementplan", "night",
            models.OneToOneField(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="plan", to="games.gamenight"),
        ),
        migrations.AddField("transfer", "payer_member", member_fk("transfers_to_pay", True)),
        migrations.AddField("transfer", "payee_member", member_fk("transfers_to_receive", True)),
        migrations.AddField(
            "payment", "night",
            models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="games.gamenight"),
        ),
        migrations.AddField("payment", "payer_member", member_fk("payments_made", True)),
        migrations.AddField("payment", "payee_member", member_fk("payments_received", True)),
        migrations.RunPython(move_to_sessions, migrations.RunPython.noop),
        migrations.RemoveField("settlementplan", "finalization"),
        migrations.RemoveField("transfer", "payer"),
        migrations.RemoveField("transfer", "payee"),
        migrations.RemoveField("payment", "session"),
        migrations.RemoveField("payment", "payer"),
        migrations.RemoveField("payment", "payee"),
        migrations.RenameField("transfer", "payer_member", "payer"),
        migrations.RenameField("transfer", "payee_member", "payee"),
        migrations.RenameField("payment", "payer_member", "payer"),
        migrations.RenameField("payment", "payee_member", "payee"),
        migrations.AlterField(
            "settlementplan", "night",
            models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="plan", to="games.gamenight"),
        ),
        migrations.AlterField("transfer", "payer", member_fk("transfers_to_pay", False)),
        migrations.AlterField("transfer", "payee", member_fk("transfers_to_receive", False)),
        migrations.AlterField(
            "payment", "night",
            models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="games.gamenight"),
        ),
    ]
