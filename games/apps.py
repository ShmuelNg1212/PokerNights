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
        from .services import lock_rsvp_nights, rsvp_member_removed

        if lock_rsvp_nights not in groups.REMOVE_LOCKS:
            groups.REMOVE_LOCKS.append(lock_rsvp_nights)
        if rsvp_member_removed not in groups.REMOVED_HOOKS:
            groups.REMOVED_HOOKS.append(rsvp_member_removed)
