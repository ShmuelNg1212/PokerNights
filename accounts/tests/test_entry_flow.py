"""The way in from an invite link: sign-up first, joining at sign-up, plain words. Rules are unchanged."""

from urllib.parse import urlencode

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from audit.models import AuditEvent
from groups import services
from groups.models import Member
from groups.tests.helpers import make_group, make_user

GOOD = {"username": "newbie", "password1": "tablestakes-91", "password2": "tablestakes-91"}


class InviteLinkTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group(group_name="Kamuning Card Club")
        self.invite, self.token = services.create_invite(self.host)
        self.invite_url = reverse("invite_accept", args=[self.token])
        self.signup, self.login = reverse("signup"), reverse("login")

    def test_signed_out_visitor_with_a_usable_invite_goes_to_sign_up(self):
        response = self.client.get(self.invite_url)
        self.assertRedirects(response, f"{self.signup}?{urlencode({'next': self.invite_url})}")
        page = self.client.get(response.url)
        self.assertContains(page, "You're invited to <strong>Kamuning Card Club</strong>")
        html = page.content.decode()
        # The way out for someone who already plays here sits beside the invitation, before the first field.
        self.assertLess(html.index("Already have an account?"), html.index('name="username"'))
        self.assertEqual(html.count("Already have an account?"), 1)
        self.assertContains(page, f"{self.login}?next={self.invite_url}")

    def test_signed_out_visitor_with_a_bad_invite_sees_the_reason_at_once(self):
        expired, token = services.create_invite(self.host)
        expired.expires_at = timezone.now()
        expired.save(update_fields=["expires_at"])
        for bad in ("not-a-token", token):
            page = self.client.get(reverse("invite_accept", args=[bad]))
            self.assertEqual(page.status_code, 404)
            self.assertContains(page, 'class="notice notice-bad" role="alert"', status_code=404)
            self.assertContains(page, reverse("login"), status_code=404)
            self.assertContains(page, "This invite link doesn't work", status_code=404)
            self.assertNotContains(page, "site-header", status_code=404)

    def test_signed_out_post_does_not_join_anyone(self):
        response = self.client.post(self.invite_url)
        self.assertRedirects(response, f"{self.login}?next={self.invite_url}")
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.use_count, 0)

    def test_sign_up_from_an_invite_joins_and_welcomes(self):
        page = self.client.post(self.signup, {**GOOD, "next": self.invite_url}, follow=True)
        self.assertRedirects(page, reverse("group", args=[self.group.pk]))
        self.assertContains(page, "Welcome to Kamuning Card Club. You&#x27;re in.")
        member = Member.objects.get(group=self.group, user__username="newbie")
        self.assertEqual((member.role, member.status, member.display_name), ("player", "active", "newbie"))
        self.invite.refresh_from_db()
        self.assertEqual(self.invite.use_count, 1)
        self.assertEqual(AuditEvent.objects.filter(action="invite.accepted", group_id=self.group.pk).count(), 1)

    def test_invite_that_stopped_working_leaves_an_account_and_explains(self):
        self.client.get(self.signup, {"next": self.invite_url})
        from groups.models import Invite
        Invite.objects.filter(pk=self.invite.pk).update(max_uses=1, use_count=1)  # someone else took the last use
        with override_settings(SIGNUP_REQUIRES_INVITE=False):
            page = self.client.post(self.signup, {**GOOD, "next": self.invite_url}, follow=True)
        self.assertTrue(get_user_model().objects.filter(username="newbie").exists())
        self.assertFalse(Member.objects.filter(group=self.group, user__username="newbie").exists())
        self.assertContains(page, "used up", status_code=404)

    @override_settings(SIGNUP_REQUIRES_INVITE=True)
    def test_used_up_invite_does_not_open_sign_up_at_all(self):
        from groups.models import Invite
        Invite.objects.filter(pk=self.invite.pk).update(max_uses=1, use_count=1)
        self.assertEqual(self.client.post(self.signup, {**GOOD, "next": self.invite_url}).status_code, 403)
        self.assertFalse(get_user_model().objects.filter(username="newbie").exists())

    def test_existing_account_is_still_asked_before_joining(self):
        self.client.force_login(make_user("ben"))
        page = self.client.get(self.invite_url)
        self.assertContains(page, "Join Kamuning Card Club")
        self.assertContains(page, "can join their games")
        self.assertContains(page, "Not now")
        self.assertFalse(Member.objects.filter(group=self.group, user__username="ben").exists())
        self.assertRedirects(self.client.post(self.invite_url), reverse("group", args=[self.group.pk]))
        self.assertTrue(Member.objects.filter(group=self.group, user__username="ben").exists())

    def test_existing_account_logging_in_from_the_link_reaches_the_confirmation(self):
        user = make_user("ben")
        user.set_password("tablestakes-91")
        user.save()
        response = self.client.post(self.login, {"username": "ben", "password": "tablestakes-91", "next": self.invite_url})
        self.assertRedirects(response, self.invite_url)
        self.assertFalse(Member.objects.filter(group=self.group, user=user).exists())

    def test_sign_up_without_an_invite_goes_home_and_joins_nothing(self):
        for target in ("", "/", "https://evil.example" + self.invite_url):
            get_user_model().objects.filter(username="newbie").delete()
            self.client.logout()
            response = self.client.post(self.signup, {**GOOD, "next": target})
            self.assertRedirects(response, reverse("home"))
            self.assertFalse(Member.objects.filter(user__username="newbie").exists())


class PlainWordsTests(TestCase):
    def setUp(self):
        make_user("hana")
        self.signup, self.login = reverse("signup"), reverse("login")

    def refused(self, **data):
        page = self.client.post(self.signup, {**GOOD, **data})
        self.assertEqual(page.status_code, 200)
        return page

    def test_each_refusal_uses_the_plain_wording(self):
        cases = [
            ({"username": "hana"}, "username", "That name is taken. Try another."),
            ({"username": "HANA"}, "username", "That name is taken. Try another."),
            ({"username": "Juan dela Cruz"}, "username", "Use letters and numbers, with no spaces."),
            ({"password1": "short1", "password2": "short1"}, "password1", "Too short. Use at least 8 characters."),
            ({"password1": "password", "password2": "password"}, "password1", "That password is too common. Pick a less usual one."),
            ({"password1": "83920174", "password2": "83920174"}, "password1", "Use more than digits."),
            ({"password1": "newbie-12", "password2": "newbie-12"}, "password1", "Too close to your username. Pick something different."),
            ({"password2": "different-91"}, "password2", "The two passwords don't match."),
        ]
        for data, field, words in cases:
            with self.subTest(words):
                page = self.refused(**data)
                self.assertIn(words, [str(e) for e in page.context["form"].errors[field]])
                self.assertFalse(get_user_model().objects.filter(username__iexact=data.get("username", "newbie")).exclude(username="hana").exists())

    def test_rules_accept_what_they_accepted_before(self):
        for index, password in enumerate(["tablestakes-91", "correct horse battery", "Zx9!qLm2"]):
            self.client.logout()
            response = self.client.post(self.signup, {"username": f"ok{index}", "password1": password, "password2": password})
            self.assertEqual(response.status_code, 302, password)

    def test_refused_sign_up_announces_once_and_focuses_the_refused_field(self):
        page = self.refused(username="hana", password1="83920174", password2="83920174")
        html = page.content.decode()
        self.assertEqual(html.count('role="alert"'), 1)
        self.assertContains(page, "Check the highlighted fields.")
        self.assertEqual(html.count("autofocus"), 1)
        self.assertRegex(html, r'<input[^>]*name="username"[^>]*autofocus')
        self.assertRegex(html, r'<input[^>]*name="username"[^>]*aria-invalid="true"')
        self.assertRegex(html, r'<input[^>]*name="password1"[^>]*aria-invalid="true"')
        self.assertNotIn('value="83920174"', html)  # a password is never written back into the page
        page = self.refused(password2="different-91")
        self.assertContains(page, "Check the highlighted field.")
        self.assertRegex(page.content.decode(), r'<input[^>]*name="password2"[^>]*autofocus')

    def test_wrong_login_says_the_same_thing_for_either_mistake(self):
        user = get_user_model().objects.get(username="hana")
        user.set_password("tablestakes-91")
        user.save()
        wrong_password = self.client.post(self.login, {"username": "hana", "password": "nope"})
        wrong_username = self.client.post(self.login, {"username": "nobody", "password": "tablestakes-91"})
        for page in (wrong_password, wrong_username):
            self.assertEqual(list(page.context["form"].non_field_errors()), ["That username and password don't match. Check capital letters."])
            html = page.content.decode()
            self.assertEqual(html.count('role="alert"'), 1)
            self.assertEqual(html.count('aria-describedby="login-error"'), 2)
            self.assertEqual(html.count('aria-invalid="true"'), 2)
            self.assertRegex(html, r'<input[^>]*name="password"[^>]*autofocus')
            self.assertNotRegex(html, r'<input[^>]*name="username"[^>]*autofocus')

    def test_fresh_pages_focus_username_and_carry_busy_labels(self):
        for url, busy in ((self.login, "Logging in…"), (self.signup, "Creating account…")):
            html = self.client.get(url).content.decode()
            self.assertRegex(html, r'<input[^>]*name="username"[^>]*autofocus')
            self.assertIn(f'data-busy="{busy}"', html)
            self.assertNotIn("aria-pressed", html)
            self.assertNotIn('role="alert"', html)

    @override_settings(SIGNUP_REQUIRES_INVITE=True)
    def test_login_offers_sign_up_only_when_it_would_open(self):
        from groups.tests.helpers import make_group
        group, host = make_group("solo", "Solo Club")
        _, token = services.create_invite(host)
        invite_url = reverse("invite_accept", args=[token])
        plain = self.client.get(self.login)
        self.assertNotContains(plain, self.signup)
        self.assertContains(plain, "Ask a host of your group for an invite link.")
        invited = self.client.get(self.login, {"next": invite_url})
        self.assertContains(invited, f"{self.signup}?next={invite_url}")
        self.assertContains(invited, "Log in, then confirm to join.")

    @override_settings(SIGNUP_REQUIRES_INVITE=True)
    def test_closed_sign_up_has_its_own_title(self):
        self.assertContains(self.client.get(self.signup), "<title>Invite needed · PokerNights</title>", status_code=403)
