"""Replace chip counts with amounts.

Until now a cash-out and a balance override were stored as chips and converted
to pesos at the session's chip rate. From here on they are amounts in the
session's unit, and no conversion exists. This migration converts the rows that
already exist to centavos and then removes the chip columns. It cannot be
reversed, because the chip counts are dropped.
"""

from math import gcd

from django.db import migrations, models


def _rate(session, SettingsVersion):
    """The session's chip rate (centavos, chips), from its lock or from its settings."""
    if session.rate_centavos:
        return session.rate_centavos, session.rate_chips
    version = SettingsVersion.objects.filter(session=session).order_by("-number").first()
    if version is None or not version.chips_per_buy_in:
        return 1, 1
    divisor = gcd(version.default_buy_in_centavos, version.chips_per_buy_in)
    return version.default_buy_in_centavos // divisor, version.chips_per_buy_in // divisor


def _spread(chip_counts, target, rate):
    """Centavo values for ``chip_counts`` that sum to ``target``: each value is
    rounded down, and the centavos left go one each to the largest remainders."""
    rate_centavos, rate_chips = rate
    parts = [divmod(chips * rate_centavos, rate_chips) for chips in chip_counts]
    values = [floor for floor, _ in parts]
    leftover = target - sum(values)
    order = sorted(range(len(values)), key=lambda i: (-parts[i][1], i))
    for step in range(abs(leftover)):
        values[order[step % len(order)]] += 1 if leftover > 0 else -1
    return values


def chips_to_amounts(apps, schema_editor):
    Session = apps.get_model("games", "GameSession")
    SettingsVersion = apps.get_model("games", "SettingsVersion")
    CashOut = apps.get_model("ledger", "CashOut")
    CashOutReversal = apps.get_model("ledger", "CashOutReversal")
    Adjustment = apps.get_model("ledger", "BalanceAdjustment")
    Finalization = apps.get_model("ledger", "Finalization")
    Result = apps.get_model("ledger", "PlayerResult")

    reversed_ids = set(CashOutReversal.objects.values_list("cash_out_id", flat=True))
    for session in Session.objects.all():
        rate = _rate(session, SettingsVersion)
        cash_outs = list(CashOut.objects.filter(session=session).order_by("id"))
        adjustments = list(Adjustment.objects.filter(session=session).order_by("id"))
        active = [row for row in cash_outs if row.pk not in reversed_ids]
        active += [row for row in adjustments if row.voided_at is None]

        def chips_of(row):
            return row.chips if hasattr(row, "chips") else row.chips_delta

        current = Finalization.objects.filter(session=session, is_current=True).first()
        if current is not None:
            # A finalized game: each player's rows must add up to the frozen cash-out value.
            targets = {r.participant_id: r.cash_out_centavos for r in Result.objects.filter(finalization=current)}
            groups = {}
            for row in active:
                groups.setdefault(row.participant_id, []).append(row)
            for participant_id, rows in groups.items():
                exact = sum(chips_of(row) for row in rows) * rate[0] // rate[1]
                values = _spread([chips_of(row) for row in rows], targets.get(participant_id, exact), rate)
                for row, value in zip(rows, values):
                    row.amount = value
        elif active:
            total = sum(chips_of(row) for row in active) * rate[0] // rate[1]
            for row, value in zip(active, _spread([chips_of(row) for row in active], total, rate)):
                row.amount = value
        active_ids = {(type(row).__name__, row.pk) for row in active}
        for row in cash_outs + adjustments:
            if (type(row).__name__, row.pk) not in active_ids:
                row.amount = chips_of(row) * rate[0] // rate[1]

        for row in cash_outs:
            row.save(update_fields=["amount"])
        for row in adjustments:
            if row.amount == 0:
                # Worth less than one centavo. An adjustment cannot be zero, so keep the row as void.
                row.amount = 1 if row.chips_delta > 0 else -1
                row.voided_at = row.voided_at or row.created_at
            row.save(update_fields=["amount", "voided_at"])

        for finalization in Finalization.objects.filter(session=session):
            for result in Result.objects.filter(finalization=finalization):
                if finalization.is_current:
                    result.adjustment = sum(
                        row.amount for row in adjustments
                        if row.voided_at is None and row.participant_id == result.participant_id
                    )
                else:
                    result.adjustment = result.adjustment_chips * rate[0] // rate[1]
                result.cashed_out = result.cash_out_centavos - result.adjustment
                result.save(update_fields=["adjustment", "cashed_out"])
            cashed = sum(Result.objects.filter(finalization=finalization).values_list("cashed_out", flat=True))
            finalization.raw_difference = cashed - finalization.total_buy_in_centavos
            finalization.settings_snapshot = [
                {key.replace("_centavos", ""): value for key, value in version.items() if key != "chips_per_buy_in"}
                for version in finalization.settings_snapshot
            ]
            finalization.save(update_fields=["raw_difference", "settings_snapshot"])


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0002_gamesession_participant_settingsversion_and_more"),
        ("ledger", "0004_finalization_playerresult_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(model_name="buyin", name="buy_in_amount_positive"),
        migrations.RemoveConstraint(model_name="buyin", name="buy_in_chips_positive"),
        migrations.RemoveConstraint(model_name="cashout", name="cash_out_chips_not_negative"),
        migrations.RemoveConstraint(model_name="balanceadjustment", name="adjustment_not_zero"),
        migrations.RemoveConstraint(model_name="finalization", name="finalization_money_conserved"),
        migrations.RemoveConstraint(model_name="playerresult", name="result_net_is_cash_out_minus_buy_ins"),
        migrations.AddField("cashout", "amount", models.BigIntegerField(default=0), preserve_default=False),
        migrations.AddField("balanceadjustment", "amount", models.BigIntegerField(default=0), preserve_default=False),
        migrations.AddField("playerresult", "cashed_out", models.BigIntegerField(default=0), preserve_default=False),
        migrations.AddField("playerresult", "adjustment", models.BigIntegerField(default=0)),
        migrations.AddField("finalization", "raw_difference", models.BigIntegerField(default=0)),
        migrations.AddField(
            "finalization", "unit",
            models.CharField(choices=[("php", "Pesos (₱)"), ("chips", "Chips")], default="php", max_length=8),
        ),
        migrations.AddField(
            "playerresult", "unit",
            models.CharField(choices=[("php", "Pesos (₱)"), ("chips", "Chips")], default="php", max_length=8),
        ),
        migrations.RunPython(chips_to_amounts, migrations.RunPython.noop),
        migrations.RemoveField("buyin", "chips"),
        migrations.RemoveField("cashout", "chips"),
        migrations.RemoveField("balanceadjustment", "chips_delta"),
        migrations.RemoveField("finalization", "chips_issued"),
        migrations.RemoveField("finalization", "raw_difference_chips"),
        migrations.RemoveField("finalization", "rate_centavos"),
        migrations.RemoveField("finalization", "rate_chips"),
        migrations.RemoveField("playerresult", "chips_cashed"),
        migrations.RemoveField("playerresult", "adjustment_chips"),
        migrations.RenameField("buyin", "amount_centavos", "amount"),
        migrations.RenameField("finalization", "total_buy_in_centavos", "total_buy_in"),
        migrations.RenameField("finalization", "total_cash_out_centavos", "total_cash_out"),
        migrations.RenameField("playerresult", "buy_in_total_centavos", "buy_in_total"),
        migrations.RenameField("playerresult", "cash_out_centavos", "cash_out"),
        migrations.RenameField("playerresult", "net_centavos", "net"),
    ]
