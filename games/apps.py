from django.apps import AppConfig


class GamesConfig(AppConfig):
    name = "games"

    def ready(self):
        from groups import services as groups

        from .services import guard_group_archive, guard_member_removal

        if guard_group_archive not in groups.ARCHIVE_GUARDS:
            groups.ARCHIVE_GUARDS.append(guard_group_archive)
        if guard_member_removal not in groups.REMOVE_GUARDS:
            groups.REMOVE_GUARDS.append(guard_member_removal)
