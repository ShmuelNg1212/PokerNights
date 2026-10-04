from django.apps import AppConfig


class GamesConfig(AppConfig):
    name = "games"

    def ready(self):
        from groups import services as groups

        from .services import guard_group_archive

        if guard_group_archive not in groups.ARCHIVE_GUARDS:
            groups.ARCHIVE_GUARDS.append(guard_group_archive)
