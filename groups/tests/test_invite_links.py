"""Invite links that can be shown again: computed from a stored salt and SECRET_KEY, never stored."""

from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from groups import services
from groups.models import Invite
from groups.tests.helpers import make_group, make_user


class InviteTokenTests(TestCase):
    def setUp(self):
        _, self.host = make_group()

    def test_the_link_can_be_made_again_and_opens_the_invite(self):
        invite, token = services.create_invite(self.host)
        self.assertTrue(invite.salt)
        self.assertNotIn(token, (invite.salt, invite.token_hash))
        self.assertEqual(services.invite_link_token(invite), token)
        self.assertEqual(services.invite_link_token(Invite.objects.get(pk=invite.pk)), token)
        self.assertEqual(services.usable_invite(token), invite)
        self.assertRegex(token, r"^[A-Za-z0-9_-]{43}$")

    def test_each_invite_has_its_own_link(self):
        first = services.create_invite(self.host)[1]
        second = services.create_invite(self.host)[1]
        self.assertNotEqual(first, second)

    def test_a_new_secret_key_leaves_the_link_working_but_unshowable(self):
        invite, token = services.create_invite(self.host)
        with self.settings(SECRET_KEY="a-different-secret-key-for-this-test-only-0123456789"):
            self.assertIsNone(services.invite_link_token(invite))
            self.assertEqual(services.usable_invite(token), invite)

    def test_an_invite_from_before_has_no_link_to_show(self):
        invite = services.create_invite(self.host)[0]
        Invite.objects.filter(pk=invite.pk).update(salt=None)
        invite.refresh_from_db()
        self.assertIsNone(services.invite_link_token(invite))

    @override_settings(INVITE_LINKS_SHOWN=False)
    def test_switch_off_stores_no_salt(self):
        invite, token = services.create_invite(self.host)
        self.assertIsNone(invite.salt)
        self.assertIsNone(services.invite_link_token(invite))
        self.assertEqual(services.usable_invite(token), invite)


class InviteEndingTests(TestCase):
    def setUp(self):
        _, self.host = make_group()

    def test_how_each_invite_ended(self):
        now = timezone.now()
        live = services.create_invite(self.host)[0]
        revoked = services.revoke_invite(self.host, services.create_invite(self.host)[0].pk)
        expired = services.create_invite(self.host)[0]
        Invite.objects.filter(pk=expired.pk).update(expires_at=now - timedelta(hours=1))
        used = services.create_invite(self.host)[0]
        Invite.objects.filter(pk=used.pk).update(use_count=used.max_uses)
        for invite, ending in ((live, None), (revoked, "revoked"), (expired, "expired"), (used, "used up")):
            invite.refresh_from_db()
            with self.subTest(ending):
                self.assertEqual(invite.ending(now), ending)

    def test_revoked_wins_over_expired(self):
        invite = services.revoke_invite(self.host, services.create_invite(self.host)[0].pk)
        self.assertEqual(invite.ending(timezone.now() + timedelta(days=30)), "revoked")

    def test_claim_and_reset_links_are_unchanged(self):
        """Still shown once: no salt, nothing to make again."""
        member = services.add_roster_player(self.host, "Ben")
        link = services.create_claim_link(self.host, member.id)[1]
        self.assertFalse(hasattr(link, "salt"))
        ben = make_user("ben")
        services.accept_invite(ben, services.create_invite(self.host)[1])
        reset = services.create_password_reset(self.host, ben.memberships.get().id)[1]
        self.assertFalse(hasattr(reset, "salt"))
