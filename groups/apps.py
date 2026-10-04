from django.apps import AppConfig


class GroupsConfig(AppConfig):
    name = "groups"

    def ready(self):
        from accounts import signup

        from .access import invite_vouches

        signup.CHECKS.append(invite_vouches)
