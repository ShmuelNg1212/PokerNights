"""Fill ``ended_at`` for sets whose play ended before the field existed.

The audit log already holds the moment a host ended play. No play period or
player interval is invented for those sets: their playing time stays
"not recorded".
"""

from django.db import migrations


def from_the_log(apps, schema_editor):
    GameSession = apps.get_model("games", "GameSession")
    AuditEvent = apps.get_model("audit", "AuditEvent")
    for game in GameSession.objects.filter(state__in=["reconciliation", "finalized"], ended_at__isnull=True):
        event = AuditEvent.objects.filter(session_id=game.pk, action="session.end").order_by("-created_at").first()
        if event is not None:
            game.ended_at = event.created_at
            game.save(update_fields=["ended_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0008_gamesession_ended_at_playinterval_playperiod"),
        ("audit", "0001_initial"),
    ]

    operations = [migrations.RunPython(from_the_log, migrations.RunPython.noop)]
