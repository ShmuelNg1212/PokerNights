from django.test import TestCase
from django.urls import reverse

from groups import services
from groups.errors import NotAllowed, RuleError
from groups.models import Member

from .helpers import add_player, make_group


class RosterTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()

    def test_host_adds_a_player_without_a_login(self):
        member = services.add_roster_player(self.host, "  Tito   Boy ", "0917")
        self.assertEqual(member.display_name, "Tito Boy")
        self.assertFalse(member.has_login)
        self.assertEqual(member.role, Member.Role.PLAYER)

    def test_duplicate_active_name_is_refused(self):
        services.add_roster_player(self.host, "Tito Boy")
        with self.assertRaises(RuleError):
            services.add_roster_player(self.host, "tito boy")
        services.remove_member(self.host, Member.objects.get(display_name="Tito Boy").pk)
        services.add_roster_player(self.host, "tito boy")

    def test_only_a_host_adds_or_renames(self):
        ben = add_player(self.group, "ben")
        with self.assertRaises(NotAllowed):
            services.add_roster_player(ben, "Guest")
        with self.assertRaises(NotAllowed):
            services.rename_member(ben, ben.pk, "Benny")

    def test_rename_checks_for_clashes(self):
        guest = services.add_roster_player(self.host, "Guest")
        add_player(self.group, "ben")
        with self.assertRaises(RuleError):
            services.rename_member(self.host, guest.pk, "BEN")
        self.assertEqual(services.rename_member(self.host, guest.pk, "Guest One").display_name, "Guest One")

    def test_a_player_without_a_login_cannot_be_host(self):
        guest = services.add_roster_player(self.host, "Guest")
        with self.assertRaises(RuleError):
            services.set_role(self.host, guest.pk, Member.Role.HOST)

    def test_add_through_the_page(self):
        self.client.force_login(self.host.user)
        response = self.client.post(reverse("member_add", args=[self.group.pk]), {"name": "Tito Boy"})
        self.assertRedirects(response, reverse("group", args=[self.group.pk]) + "?view=settings#players")
        self.assertContains(self.client.get(reverse("group", args=[self.group.pk]), {"view": "settings"}), "Tito Boy")
        self.assertNotContains(self.client.get(reverse("group", args=[self.group.pk])), "Tito Boy")
