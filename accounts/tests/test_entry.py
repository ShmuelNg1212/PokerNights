"""The entry pages: what a signed-out person sees on the way in. Authentication itself is tested elsewhere."""

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from groups import services
from groups.tests.helpers import add_player, make_group, make_user

LINE = "Keeps the books for your home poker game"


class EntryPagesTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group(group_name="Kamuning <Card> Club")
        self.invite, token = services.create_invite(self.host)
        self.invite_url = reverse("invite_accept", args=[token])
        self.login, self.signup = reverse("login"), reverse("signup")

    def test_login_is_the_front_door(self):
        page = self.client.get(self.login)
        self.assertContains(page, 'class="page entry-page"')
        self.assertContains(page, "branding/logo-mark.svg")
        self.assertContains(page, LINE)
        self.assertContains(page, "<h1>Log in</h1>")
        self.assertContains(page, 'class="btn btn-primary btn-block"')
        self.assertNotContains(page, "site-header")
        self.assertNotContains(page, "You're invited")
        self.assertContains(page, 'autocomplete="username"')
        self.assertContains(page, 'autocomplete="current-password"')
        self.assertContains(page, "data-password-toggle", count=1)
        self.assertContains(page, "js/password.js")

    def test_usable_invite_names_the_group_on_login_and_signup(self):
        for url in (self.login, self.signup):
            page = self.client.get(url, {"next": self.invite_url})
            self.assertContains(page, "You're invited to <strong>Kamuning &lt;Card&gt; Club</strong>")
            self.assertNotContains(page, "<Card>")
            self.assertContains(page, f'name="next" value="{self.invite_url}"')

    def test_login_link_to_signup_keeps_the_invite(self):
        page = self.client.get(self.login, {"next": self.invite_url})
        self.assertContains(page, f'{self.signup}?next={self.invite_url}')

    def test_no_group_is_named_for_a_bad_or_foreign_next(self):
        for target in ("/", "/join/not-a-token/", "https://evil.example" + self.invite_url, "/g/1/"):
            for url in (self.login, self.signup):
                self.assertNotContains(self.client.get(url, {"next": target}), "You're invited")

    def test_no_group_is_named_once_the_invite_stops_working(self):
        states = [{"expires_at": timezone.now()}, {"use_count": self.invite.max_uses}, {"revoked_at": timezone.now()}]
        for change in states:
            fresh, token = services.create_invite(self.host)
            for field, value in change.items():
                setattr(fresh, field, value)
            fresh.save()
            page = self.client.get(self.login, {"next": reverse("invite_accept", args=[token])})
            self.assertNotContains(page, "You're invited")

    def test_wrong_login_shows_one_notice_and_keeps_the_username(self):
        make_user("hana2")
        page = self.client.post(self.login, {"username": "hana2", "password": "wrong"})
        self.assertContains(page, 'class="notice notice-bad" role="alert"', count=1)
        self.assertContains(page, "That username and password don&#x27;t match. Check capital letters.")
        self.assertContains(page, "Forgot your password? Ask a host of your group for a reset link.")
        self.assertContains(page, 'value="hana2"')
        self.assertNotContains(page, 'value="wrong"')

    @override_settings(RESET_LINKS=False)
    def test_entry_pages_fall_back_when_reset_links_are_off(self):
        page = self.client.post(self.login, {"username": "nobody", "password": "wrong"})
        self.assertContains(page, "Forgot your password? There is no reset yet.")
        self.assertContains(self.client.get(self.signup), "<strong>There is no password reset yet.</strong>")

    def test_signup_has_short_help_and_plain_labels(self):
        page = self.client.get(self.signup)
        self.assertContains(page, "<h1>Create your account</h1>")
        self.assertContains(page, "Your friends see this name. Letters and numbers, no spaces.")
        self.assertContains(page, "At least 8 characters, not a common password, not only digits, and not like your username.")
        self.assertContains(page, "Forgot it later? A host of your group can send you a reset link.")
        self.assertNotContains(page, "There is no password reset yet.")
        self.assertContains(page, "Repeat password")
        self.assertNotContains(page, "Password confirmation")
        self.assertNotContains(page, "<ul>")  # the stock four-bullet rule list is gone
        self.assertNotContains(page, "for verification")
        self.assertContains(page, 'autocomplete="new-password"', count=2)
        self.assertContains(page, "data-password-toggle", count=1)
        self.assertContains(page, LINE)  # an invited newcomer lands here first
        self.assertContains(page, "It never moves money.")
        self.assertNotContains(page, "site-header")

    def test_refused_signup_names_the_broken_rule_and_keeps_the_username(self):
        page = self.client.post(self.signup, {"username": "newbie", "password1": "12345678", "password2": "12345678"})
        self.assertContains(page, "Use more than digits.")
        self.assertEqual(list(page.context["form"].errors), ["password1"])  # reported where the rule is stated
        self.assertContains(page, 'value="newbie"')
        self.assertNotContains(page, 'value="12345678"')
        page = self.client.post(self.signup, {"username": "newbie", "password1": "tablestakes-91", "password2": "other"})
        self.assertContains(page, "The two passwords don&#x27;t match.")
        self.assertEqual(list(page.context["form"].errors), ["password2"])

    def test_password_rules_are_unchanged(self):
        from django.contrib.auth import get_user_model
        for bad in ("short1", "password", "12345678", "newbie-1"):
            self.client.post(self.signup, {"username": "newbie", "password1": bad, "password2": bad})
        self.assertFalse(get_user_model().objects.filter(username="newbie").exists())
        response = self.client.post(self.signup, {"username": "newbie", "password1": "tablestakes-91", "password2": "tablestakes-91"})
        self.assertRedirects(response, reverse("home"))

    @override_settings(SIGNUP_REQUIRES_INVITE=True)
    def test_closed_signup_keeps_its_status_and_uses_the_frame(self):
        page = self.client.get(self.signup)
        self.assertEqual(page.status_code, 403)
        self.assertContains(page, 'class="page entry-page"', status_code=403)
        self.assertContains(page, LINE, status_code=403)
        self.assertContains(page, "Sign-up needs an invite", status_code=403)

    def test_join_page_shows_the_group_and_player_count(self):
        add_player(self.group, "ben")
        self.client.force_login(make_user("newcomer"))
        page = self.client.get(self.invite_url)
        self.assertContains(page, "Join Kamuning &lt;Card&gt; Club")
        self.assertContains(page, "2 players")
        self.assertContains(page, "site-header")  # signed in: the header with Log out stays
        self.assertContains(page, 'class="page entry-page"')
        page = self.client.get(reverse("invite_accept", args=["not-a-token"]))
        self.assertContains(page, "not valid", status_code=404)
