"""The front door's frame and the arrival the server chooses for it. The words on each page are in test_entry.py."""

from django.contrib.sessions.models import Session
from django.test import TestCase, override_settings
from django.urls import reverse

from groups import services
from groups.tests.helpers import make_group

COOKIE = "door"


class DoorFrameTests(TestCase):
    def setUp(self):
        self.group, self.host = make_group(group_name="Kamuning Card Club")
        _, token = services.create_invite(self.host)
        self.invite_url = reverse("invite_accept", args=[token])
        self.login, self.signup = reverse("login"), reverse("signup")

    def test_log_in_has_the_tall_hero_and_the_sheet(self):
        page = self.client.get(self.login).content.decode()
        self.assertIn('class="door-hero"', page)
        self.assertIn('class="door-mark"', page)
        self.assertIn('class="door-ring"', page)
        self.assertIn('class="door-moon"', page)
        self.assertIn('<section class="door-sheet">', page)
        # The task is inside the sheet; the brand is above it.
        self.assertLess(page.index('class="door-hero"'), page.index('class="door-sheet"'))
        self.assertLess(page.index('class="door-sheet"'), page.index("<h1>Log in</h1>"))
        self.assertLess(page.index("Keeps the books"), page.index('class="door-sheet"'))

    def test_sign_up_has_the_row_hero_and_the_description_at_the_foot(self):
        page = self.client.get(self.signup).content.decode()
        self.assertIn('class="door-hero door-hero-row"', page)
        self.assertLess(page.index("Create account</button>"), page.index("It never moves money."))
        self.assertIn('class="door-foot"', page)

    def test_an_invited_sign_up_leads_with_the_group(self):
        page = self.client.get(self.signup, {"next": self.invite_url})
        self.assertContains(page, "<h1>Join Kamuning Card Club</h1>")
        self.assertContains(page, "Create your account to get in.")
        self.assertContains(page, "Already have an account?")
        self.assertNotContains(page, "<h1>Create your account</h1>")

    def test_the_mark_is_decoration_and_the_name_is_text(self):
        page = self.client.get(self.login).content.decode()
        mark = page[page.index("<svg"):page.index("</svg>")]
        self.assertIn('aria-hidden="true"', mark)
        self.assertIn('<p class="entry-name">PokerNights</p>', page)

    def test_what_a_password_manager_reads_is_unchanged(self):
        page = self.client.get(self.login)
        for part in ('name="username"', 'autocomplete="username"', 'name="password"', 'autocomplete="current-password"', '<form method="post"'):
            self.assertContains(page, part)
        page = self.client.get(self.signup)
        for part in ('name="username"', 'name="password1"', 'name="password2"', 'autocomplete="new-password"', '<form method="post"'):
            self.assertContains(page, part)
        self.assertNotContains(page, 'data-turbo="true"')

    def test_the_phone_keyboard_says_next_then_go(self):
        page = self.client.get(self.login).content.decode()
        self.assertEqual(page.count('enterkeyhint="next"'), 1)
        self.assertEqual(page.count('enterkeyhint="go"'), 1)
        page = self.client.get(self.signup).content.decode()
        self.assertEqual(page.count('enterkeyhint="next"'), 2)
        self.assertEqual(page.count('enterkeyhint="go"'), 1)

    def test_every_front_door_screen_uses_the_frame(self):
        for url, status in ((self.login, 200), (self.signup, 200), (reverse("invite_accept", args=["nope"]), 404),
                            (reverse("password_reset", args=["nope"]), 404)):
            with self.subTest(url=url):
                page = self.client.get(url)
                self.assertContains(page, 'class="door-sheet"', status_code=status)
                self.assertContains(page, 'class="door-mark"', status_code=status)
        with override_settings(SIGNUP_REQUIRES_INVITE=True):
            self.assertContains(self.client.get(self.signup), 'class="door-sheet"', status_code=403)
        self.client.force_login(self.host.user)
        page = self.client.get(self.invite_url)
        self.assertContains(page, 'class="door-sheet"')
        self.assertContains(page, "site-header")


class DoorArrivalTests(TestCase):
    def setUp(self):
        self.login, self.signup = reverse("login"), reverse("signup")

    def test_the_first_visit_gets_the_full_arrival_and_the_cookie(self):
        page = self.client.get(self.login)
        self.assertContains(page, 'data-arrival="full"')
        cookie = page.cookies[COOKIE]
        self.assertEqual(cookie.value, "1")
        self.assertEqual(cookie["max-age"], "")
        self.assertEqual(cookie["expires"], "")
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(cookie["path"], "/")

    def test_later_visits_in_the_session_get_the_short_arrival(self):
        self.client.get(self.login)
        for url in (self.login, self.signup):
            page = self.client.get(url)
            self.assertContains(page, 'data-arrival="short"')
            self.assertNotIn(COOKIE, page.cookies)

    def test_a_refused_page_plays_no_arrival(self):
        page = self.client.post(self.login, {"username": "nobody", "password": "wrong"})
        self.assertNotContains(page, "data-arrival")
        page = self.client.post(self.signup, {"username": "", "password1": "x", "password2": "y"})
        self.assertNotContains(page, "data-arrival")

    def test_nothing_is_written_for_a_signed_out_visitor(self):
        self.client.get(self.login)
        self.client.get(self.signup)
        self.assertEqual(Session.objects.count(), 0)

    def test_a_page_outside_the_front_door_sets_no_cookie(self):
        _, host = make_group()
        self.client.force_login(host.user)
        page = self.client.get(reverse("home"))
        self.assertNotIn(COOKIE, page.cookies)
        self.assertNotContains(page, "data-arrival")

    @override_settings(SESSION_COOKIE_SECURE=True)
    def test_the_cookie_is_secure_where_the_session_cookie_is(self):
        self.assertTrue(self.client.get(self.login).cookies[COOKIE]["secure"])

    def test_the_switch_removes_the_movement_and_keeps_the_frame(self):
        with override_settings(DOOR_MOTION=False):
            page = self.client.get(self.login)
            self.assertNotContains(page, "data-arrival")
            self.assertNotContains(page, 'data-door="on"')
            self.assertNotIn(COOKIE, page.cookies)
            self.assertContains(page, 'class="door-sheet"')
        self.assertContains(self.client.get(self.login), 'data-door="on"')
