from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from groups import services
from groups.errors import NotAllowed, RuleError
from groups.models import Invite, Member

from .helpers import add_player, make_group, make_user


class InviteTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.invite, self.token = services.create_invite(self.host)

    def test_token_is_stored_only_as_a_hash(self):
        self.assertNotEqual(self.invite.token_hash, self.token)
        self.assertEqual(self.invite.token_hash, services.hash_token(self.token))

    def test_accept_makes_a_player_and_repeat_changes_nothing(self):
        ben = make_user("ben")
        member = services.accept_invite(ben, self.token)
        self.assertEqual((member.role, member.status), (Member.Role.PLAYER, Member.Status.ACTIVE))
        again = services.accept_invite(ben, self.token)
        self.assertEqual(again.pk, member.pk)
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.use_count, 1)
        self.assertEqual(Member.objects.filter(group=self.group, user=ben).count(), 1)

    def test_expired_revoked_and_used_up_invites_are_refused(self):
        ben = make_user("ben")
        Invite.objects.filter(pk=self.invite.pk).update(expires_at=timezone.now() - timedelta(minutes=1))
        with self.assertRaises(RuleError):
            services.accept_invite(ben, self.token)
        Invite.objects.filter(pk=self.invite.pk).update(expires_at=timezone.now() + timedelta(days=1), max_uses=1, use_count=1)
        with self.assertRaises(RuleError):
            services.accept_invite(ben, self.token)
        Invite.objects.filter(pk=self.invite.pk).update(use_count=0)
        services.revoke_invite(self.host, self.invite.pk)
        with self.assertRaises(RuleError):
            services.accept_invite(ben, self.token)
        with self.assertRaises(RuleError):
            services.accept_invite(ben, "not-a-token")
        self.assertFalse(Member.objects.filter(user=ben).exists())

    def test_only_a_host_creates_or_revokes(self):
        ben = add_player(self.group, "ben")
        with self.assertRaises(NotAllowed):
            services.create_invite(ben)
        with self.assertRaises(NotAllowed):
            services.revoke_invite(ben, self.invite.pk)

    def test_removed_member_can_return_through_an_invite(self):
        ben = add_player(self.group, "ben")
        services.remove_member(self.host, ben.pk)
        member = services.accept_invite(ben.user, self.token)
        self.assertEqual((member.pk, member.status), (ben.pk, Member.Status.ACTIVE))

    def test_name_clash_with_a_roster_player_gets_a_suffix(self):
        Member.objects.create(group=self.group, display_name="ben")
        member = services.accept_invite(make_user("ben"), self.token)
        self.assertEqual(member.display_name, "ben (2)")


class InviteViewTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()

    def test_host_sees_the_link_once(self):
        self.client.force_login(self.host.user)
        self.client.post(reverse("invite_create", args=[self.group.pk]))
        # The link waits for the settings view; another tab does not use it up.
        self.assertNotContains(self.client.get(reverse("group", args=[self.group.pk])), "/join/")
        page = self.client.get(reverse("group", args=[self.group.pk]), {"view": "settings"})
        self.assertContains(page, "/join/")
        self.assertNotContains(self.client.get(reverse("group", args=[self.group.pk]), {"view": "settings"}), "/join/")

    def test_new_user_signs_up_from_the_link_and_joins(self):
        _, token = services.create_invite(self.host)
        url = reverse("invite_accept", args=[token])
        response = self.client.get(url)
        self.assertRedirects(response, f"{reverse('login')}?next={url}")
        response = self.client.post(
            reverse("signup"),
            {"username": "newbie", "password1": "tablestakes-91", "password2": "tablestakes-91", "next": url},
        )
        self.assertRedirects(response, url)
        response = self.client.post(url)
        self.assertRedirects(response, reverse("group", args=[self.group.pk]))
        self.assertTrue(Member.objects.filter(group=self.group, user__username="newbie").exists())

    def test_bad_link_shows_not_valid(self):
        self.client.force_login(make_user("ben"))
        response = self.client.get(reverse("invite_accept", args=["nope"]))
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "not valid", status_code=404)
