"""Put every existing game into a session of its own, as set number 1."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def one_night_per_game(apps, schema_editor):
    GameNight = apps.get_model("games", "GameNight")
    GameSession = apps.get_model("games", "GameSession")
    for game in GameSession.objects.all():
        done = game.state in ("finalized", "canceled")
        night = GameNight.objects.create(
            group_id=game.group_id, table_id=game.table_id, game_date=game.game_date, location=game.location,
            game_type=game.game_type, unit=game.unit, status="closed" if done else "open",
            created_by_id=game.created_by_id, closed_at=game.finalized_at if done else None,
        )
        GameNight.objects.filter(pk=night.pk).update(created_at=game.created_at)
        game.night_id = night.pk
        game.set_number = 1
        game.save(update_fields=["night", "set_number"])


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0005_participantbatch"),
        ("groups", "0002_invite"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GameNight",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("game_date", models.DateField()),
                ("location", models.CharField(blank=True, max_length=120)),
                ("game_type", models.CharField(choices=[("nlh", "No-Limit Hold'em"), ("plo", "Pot-Limit Omaha"), ("other", "Other")], default="nlh", max_length=8)),
                ("unit", models.CharField(choices=[("php", "Pesos (₱)"), ("chips", "Chips")], default="php", max_length=8)),
                ("status", models.CharField(choices=[("open", "Open"), ("closed", "Closed")], default="open", max_length=8)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="+", to=settings.AUTH_USER_MODEL)),
                ("group", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="nights", to="groups.gamegroup")),
                ("table", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="nights", to="games.table")),
            ],
            options={"ordering": ["-game_date", "-id"]},
        ),
        migrations.AddField(
            model_name="gamesession", name="night",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name="sets", to="games.gamenight"),
        ),
        migrations.AddField(model_name="gamesession", name="set_number", field=models.PositiveIntegerField(default=1)),
        migrations.RunPython(one_night_per_game, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="gamesession", name="night",
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="sets", to="games.gamenight"),
        ),
    ]
