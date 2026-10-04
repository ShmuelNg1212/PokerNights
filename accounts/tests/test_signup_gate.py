from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from groups import services
from groups.models import Member
from groups.tests.helpers import make_group

DATA = {"username": "newbie", "password1": "tablestakes-91", "password2": "tablestakes-91"}


@override_settings(SIGNUP_REQUIRES_INVITE=True)
class InviteOnlySignupTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group()
        self.invite, token = services.create_invite(self.host)
        self.invite_url = reverse("invite_accept", args=[token])
        self.url = reverse("signup")

    def users(self):
        return get_user_model().objects.count()

    def test_without_an_invite_there_is_no_form_and_no_account(self):
        before = self.users()
        for query in ({}, {"next": "/"}, {"next": "/join/not-a-token/"}, {"next": "https://evil.example/join/x/"}):
            page = self.client.get(self.url, query)
            self.assertEqual(page.status_code, 403)
            self.assertContains(page, "Sign-up needs an invite", status_code=403)
            self.assertNotContains(page, "<form method=\"post\" class=\"form-section", status_code=403)
            self.assertEqual(self.client.post(self.url, {**DATA, **query}).status_code, 403)
        self.assertEqual(self.users(), before)

    def test_a_usable_invite_opens_sign_up_and_leads_to_joining(self):
        self.assertContains(self.client.get(self.url, {"next": self.invite_url}), "Create account")
        response = self.client.post(self.url, {**DATA, "next": self.invite_url})
        # An account created from an invite joins that group at once.
        self.assertRedirects(response, reverse("group", args=[self.group.pk]))
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.use_count, 1)
        self.assertTrue(Member.objects.filter(group=self.group, user__username="newbie").exists())

    def test_revoked_expired_and_used_up_invites_do_not_open_sign_up(self):
        def refused():
            return self.client.post(self.url, {**DATA, "next": self.invite_url}).status_code == 403
        self.invite.expires_at = timezone.now()
        self.invite.save(update_fields=["expires_at"])
        self.assertTrue(refused())
        self.invite.expires_at = timezone.now() + timezone.timedelta(days=1)
        self.invite.use_count = self.invite.max_uses
        self.invite.save(update_fields=["expires_at", "use_count"])
        self.assertTrue(refused())
        self.invite.use_count = 0
        self.invite.save(update_fields=["use_count"])
        services.revoke_invite(self.host, self.invite.pk)
        self.assertTrue(refused())
        self.assertFalse(get_user_model().objects.filter(username="newbie").exists())

    def test_the_whole_invite_flow_from_a_logged_out_browser(self):
        from urllib.parse import urlencode
        response = self.client.get(self.invite_url)
        signup_url = f"{self.url}?{urlencode({'next': self.invite_url})}"
        self.assertRedirects(response, signup_url)  # a signed-out visitor is a newcomer
        page = self.client.get(signup_url)
        self.assertContains(page, "Create account")
        self.assertContains(page, f"{reverse('login')}?next=")


@override_settings(SIGNUP_REQUIRES_INVITE=False)
class OpenSignupTests(TestCase):
    def test_sign_up_stays_open_when_the_setting_is_off(self):
        self.assertContains(self.client.get(reverse("signup")), "Create account")
        self.assertRedirects(self.client.post(reverse("signup"), DATA), reverse("home"))
