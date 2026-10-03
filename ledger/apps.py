from django.apps import AppConfig


class LedgerConfig(AppConfig):
    name = "ledger"

    def ready(self):
        from games import services as games

        from games import clock

        from .services import (
            back_in_play, guard_participant_exit, is_cashed_out, session_has_money, void_counts_on_resume,
        )

        if guard_participant_exit not in games.PARTICIPANT_EXIT_GUARDS:
            games.PARTICIPANT_EXIT_GUARDS.append(guard_participant_exit)
        if session_has_money not in games.SESSION_MONEY_CHECKS:
            games.SESSION_MONEY_CHECKS.append(session_has_money)
        if void_counts_on_resume not in games.RESUME_HOOKS:
            games.RESUME_HOOKS.append(void_counts_on_resume)
        if back_in_play not in games.RETURN_HOOKS:
            games.RETURN_HOOKS.append(back_in_play)
        if is_cashed_out not in clock.SKIP_ON_RESUME:
            clock.SKIP_ON_RESUME.append(is_cashed_out)
