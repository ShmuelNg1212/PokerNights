from django.contrib.auth import get_user_model

from groups import services
from groups.models import Member


def make_user(name):
    return get_user_model().objects.create_user(name, password="tablestakes-91")


def make_group(host_name="hana", group_name="Friday Game"):
    """A group with one host. Returns (group, host_member)."""
    host = services.create_group(make_user(host_name), group_name)
    return host.group, host


def add_player(group, name, *, role=Member.Role.PLAYER):
    """A member with a login."""
    return Member.objects.create(group=group, user=make_user(name), display_name=name, role=role)
