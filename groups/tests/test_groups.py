from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from groups import services
from groups.errors import NotAllowed, RuleError
from groups.models import Member

from .helpers import add_player, make_group, make_user


class GroupServiceTests(TestCase):
    def test_creator_becomes_host(self):
        group, host = make_group()
        self.assertTrue(host.is_host)
        self.assertEqual(group.members.count(), 1)

    def test_group_name_is_required(self):
        with self.assertRaises(RuleError):
            services.create_group(make_user("ana"), "   ")

    def test_one_membership_per_user_per_group(self):
        group, host = make_group()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Member.objects.create(group=group, user=host.user, display_name="again")

    def test_active_names_are_unique_ignoring_case(self):
        group, _ = make_group()
        Member.objects.create(group=group, display_name="Tito Boy")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Member.objects.create(group=group, display_name="tito boy")

    def test_only_a_host_changes_roles(self):
        group, host = make_group()
        ben = add_player(group, "ben")
        cy = add_player(group, "cy")
        with self.assertRaises(NotAllowed):
            services.set_role(ben, cy.pk, Member.Role.HOST)
        services.set_role(host, ben.pk, Member.Role.HOST)
        ben.refresh_from_db()
        self.assertTrue(ben.is_host)

    def test_last_host_cannot_be_demoted_or_removed(self):
        group, host = make_group()
        with self.assertRaises(RuleError):
            services.set_role(host, host.pk, Member.Role.PLAYER)
        with self.assertRaises(RuleError):
            services.remove_member(host, host.pk)
        ben = add_player(group, "ben", role=Member.Role.HOST)
        services.set_role(ben, host.pk, Member.Role.PLAYER)
        host.refresh_from_db()
        self.assertFalse(host.is_host)

    def test_member_of_another_group_cannot_be_changed(self):
        _, host = make_group()
        other_group, _ = make_group("omar", "Other")
        stranger = add_player(other_group, "sam")
        with self.assertRaises(RuleError):
            services.set_role(host, stranger.pk, Member.Role.HOST)


class GroupViewTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.ben = add_player(self.group, "ben")

    def test_create_group_from_home(self):
        self.client.force_login(make_user("zed"))
        response = self.client.post(reverse("group_create"), {"name": "Zed's Game"})
        member = Member.objects.get(user__username="zed")
        self.assertRedirects(response, reverse("group", args=[member.group_id]))
        self.assertTrue(member.is_host)

    def test_member_sees_group_and_non_member_gets_404(self):
        self.client.force_login(self.ben.user)
        self.assertContains(self.client.get(reverse("group", args=[self.group.pk])), "Friday Game")
        self.client.force_login(make_user("stranger"))
        self.assertEqual(self.client.get(reverse("group", args=[self.group.pk])).status_code, 404)
        response = self.client.post(reverse("member_remove", args=[self.group.pk, self.ben.pk]))
        self.assertEqual(response.status_code, 404)

    def test_removed_member_loses_access(self):
        services.remove_member(self.host, self.ben.pk)
        self.client.force_login(self.ben.user)
        self.assertEqual(self.client.get(reverse("group", args=[self.group.pk])).status_code, 404)

    def test_player_cannot_post_host_actions(self):
        self.client.force_login(self.ben.user)
        response = self.client.post(reverse("member_role", args=[self.group.pk, self.ben.pk]), {"role": "host"})
        self.assertEqual(response.status_code, 403)
        self.ben.refresh_from_db()
        self.assertFalse(self.ben.is_host)

    def test_home_lists_only_my_groups(self):
        make_group("omar", "Secret Game")
        self.client.force_login(self.ben.user)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Friday Game")
        self.assertNotContains(response, "Secret Game")
