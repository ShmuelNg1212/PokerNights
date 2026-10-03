from django.apps import AppConfig


class LedgerConfig(AppConfig):
    name = "ledger"

    def ready(self):
        from games import services as games

        from .services import guard_participant_exit

        if guard_participant_exit not in games.PARTICIPANT_EXIT_GUARDS:
            games.PARTICIPANT_EXIT_GUARDS.append(guard_participant_exit)
