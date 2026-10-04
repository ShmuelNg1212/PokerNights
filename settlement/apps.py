from django.apps import AppConfig


class SettlementConfig(AppConfig):
    name = "settlement"

    def ready(self):
        from games import services as games

        from .queries import night_has_records

        if night_has_records not in games.NIGHT_RECORD_CHECKS:
            games.NIGHT_RECORD_CHECKS.append(night_has_records)
