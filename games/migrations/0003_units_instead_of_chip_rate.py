"""Give presets and sessions a unit, and remove the chip rate and chips per buy-in.

Runs after the ledger migration that converts chip counts, because that
conversion reads the chip rate removed here.
"""

from django.db import migrations, models

UNIT = dict(choices=[("php", "Pesos (₱)"), ("chips", "Chips")], default="php", max_length=8)
STAKES = ("small_blind", "big_blind", "min_buy_in", "max_buy_in", "default_buy_in")


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0002_gamesession_participant_settingsversion_and_more"),
        ("ledger", "0005_amounts_instead_of_chips"),
    ]

    operations = [
        *[
            migrations.RemoveConstraint(model_name=model, name=f"{prefix}_{name}")
            for model, prefix in (("settingspreset", "preset"), ("settingsversion", "settings"))
            for name in ("blinds_valid", "buy_in_range_valid", "chips_positive")
        ],
        migrations.RemoveConstraint(model_name="gamesession", name="session_rate_both_or_neither"),
        migrations.AddField("settingspreset", "unit", models.CharField(**UNIT)),
        migrations.AddField("gamesession", "unit", models.CharField(**UNIT)),
        migrations.RemoveField("settingspreset", "chips_per_buy_in"),
        migrations.RemoveField("settingsversion", "chips_per_buy_in"),
        migrations.RemoveField("gamesession", "rate_centavos"),
        migrations.RemoveField("gamesession", "rate_chips"),
        *[
            migrations.RenameField(model, f"{name}_centavos", name)
            for model in ("settingspreset", "settingsversion")
            for name in STAKES
        ],
    ]
