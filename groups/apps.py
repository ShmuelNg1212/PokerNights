from django.apps import AppConfig


class GroupsConfig(AppConfig):
    name = "groups"

    def ready(self):
        from accounts import signup

        from .access import invite_group_name, invite_vouches, join_from_invite

        signup.CHECKS.append(invite_vouches)
        signup.INVITERS.append(invite_group_name)
        signup.AFTER_SIGNUP.append(join_from_invite)
