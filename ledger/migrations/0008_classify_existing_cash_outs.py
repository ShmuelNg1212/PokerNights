"""Classify cash-outs that existed before ``kind``.

A cash-out is final if the player has left or the set's play has ended.
A cash-out of a player who is still at a running table is partial.
"""

from django.db import migrations


def classify(apps, schema_editor):
    CashOut = apps.get_model("ledger", "CashOut")
    CashOut.objects.update(kind="final")
    CashOut.objects.filter(session__state__in=["open", "running"], participant__status="joined").update(kind="partial")


class Migration(migrations.Migration):

    dependencies = [("ledger", "0007_cashout_kind_finalcount_cashout_final_count_and_more")]

    operations = [migrations.RunPython(classify, migrations.RunPython.noop)]
