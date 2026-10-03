from django.apps import AppConfig


class LedgerConfig(AppConfig):
    name = "ledger"

    def ready(self):
        from games import services as games

        from .services import guard_participant_exit, session_has_money

        if guard_participant_exit not in games.PARTICIPANT_EXIT_GUARDS:
            games.PARTICIPANT_EXIT_GUARDS.append(guard_participant_exit)
        if session_has_money not in games.SESSION_MONEY_CHECKS:
            games.SESSION_MONEY_CHECKS.append(session_has_money)
