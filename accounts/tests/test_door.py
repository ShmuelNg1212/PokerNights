"""The front door's frame and the arrival the server chooses for it. The words on each page are in test_entry.py."""

import re

from django.contrib.sessions.models import Session
from django.test import TestCase, override_settings
from django.urls import reverse

from groups import services
from groups.tests.helpers import make_group, make_user

COOKIE = "door"
ARRIVED = "arrived"


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
        self.assertNotIn("Keeps the books", page)

    def test_sign_up_has_the_row_hero_and_the_description_under_the_heading(self):
        page = self.client.get(self.signup).content.decode()
        self.assertIn('class="door-hero door-hero-row"', page)
        self.assertLess(page.index("<h1>"), page.index("It never moves money."))
        self.assertLess(page.index("It never moves money."), page.index("<form"))

    def test_an_invited_sign_up_leads_with_the_group(self):
        page = self.client.get(self.signup, {"next": self.invite_url})
        self.assertContains(page, "<h1>Join Kamuning Card Club</h1>")
        self.assertContains(page, "invited you")
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
        for part in ('name="username"', 'name="password1"', 'autocomplete="new-password"', '<form method="post"'):
            self.assertContains(page, part)
        self.assertNotContains(page, 'name="password2"')  # one new password; the manager offers to save it
        self.assertNotContains(page, 'data-turbo="true"')

    def test_the_phone_keyboard_says_next_then_go(self):
        page = self.client.get(self.login).content.decode()
        self.assertEqual(page.count('enterkeyhint="next"'), 1)
        self.assertEqual(page.count('enterkeyhint="go"'), 1)
        page = self.client.get(self.signup).content.decode()
        self.assertEqual(page.count('enterkeyhint="next"'), 1)  # username; the one password field sends
        self.assertRegex(page, r'<input[^>]*name="password1"[^>]*enterkeyhint="go"')

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


class WelcomeTests(TestCase):
    """The one page after a successful login plays the arrival into the app."""

    def setUp(self):
        self.group, self.host = make_group(group_name="Kamuning Card Club")
        self.login, self.signup, self.home = reverse("login"), reverse("signup"), reverse("home")

    def log_in(self, **extra):
        return self.client.post(self.login, {"username": "hana", "password": "tablestakes-91", **extra})

    def test_the_page_after_a_login_is_the_arrival_and_only_that_page(self):
        answer = self.log_in()
        cookie = answer.cookies[ARRIVED]
        self.assertEqual((cookie.value, cookie["max-age"], cookie["samesite"], cookie["path"]), ("1", 30, "Lax", "/"))
        page = self.client.get(self.home)
        self.assertContains(page, 'class="page hub-page home-page" data-depth="0" data-alerts-remind data-welcome data-came-in>')
        self.assertEqual(page.cookies[ARRIVED].value, "")  # removed by the page that read it
        self.assertEqual(page.cookies[ARRIVED]["max-age"], 0)
        for _ in range(2):  # a reload, a later visit
            again = self.client.get(self.home)
            self.assertNotContains(again, "data-welcome")
            self.assertNotIn(ARRIVED, again.cookies)

    def test_the_page_a_person_was_sent_from_is_the_arrival(self):
        target = reverse("group", args=[self.group.pk])
        self.assertRedirects(self.log_in(next=target), target, fetch_redirect_response=False)
        self.assertContains(self.client.get(target), "data-welcome")
        self.assertNotContains(self.client.get(self.home), "data-welcome")

    def test_sign_up_is_an_arrival_too(self):
        answer = self.client.post(self.signup, {"username": "newcomer", "password1": "tablestakes-91", "password2": "tablestakes-91"})
        self.assertEqual(answer.cookies[ARRIVED].value, "1")
        page = self.client.get(self.home)
        self.assertContains(page, "Start your first group")
        self.assertContains(page, "data-welcome")

    def test_a_reset_link_is_an_arrival_too(self):
        from accounts import services as accounts

        player = make_user("pedro")
        _, token = accounts.issue_reset_link(player, created_by=self.host.user, group_id=self.group.pk)
        answer = self.client.post(reverse("password_reset", args=[token]), {"new_password1": "another-stack-77", "new_password2": "another-stack-77"})
        self.assertEqual(answer.cookies[ARRIVED].value, "1")
        self.assertContains(self.client.get(self.home), "data-welcome")

    def test_a_refused_login_is_no_arrival(self):
        answer = self.client.post(self.login, {"username": "hana", "password": "wrong"})
        self.assertNotIn(ARRIVED, answer.cookies)
        self.assertNotContains(answer, "data-welcome")

    def test_a_front_door_screen_leaves_the_arrival_for_the_page_behind_it(self):
        # An existing account that logs in from an invite is asked to confirm first, on a front-door screen.
        other, _ = make_group(host_name="rosa", group_name="Other Club")
        from groups import services
        _, token = services.create_invite(_)
        invite = reverse("invite_accept", args=[token])
        self.log_in(next=invite)
        page = self.client.get(invite)
        self.assertNotContains(page, "data-welcome")
        self.assertNotIn(ARRIVED, page.cookies)
        self.assertContains(self.client.get(self.home), "data-welcome")

    def test_a_page_fetched_ahead_of_a_tap_does_not_use_it_up(self):
        self.log_in()
        ahead = self.client.get(self.home, headers={"X-Sec-Purpose": "prefetch"})
        self.assertNotContains(ahead, "data-welcome")
        self.assertNotIn(ARRIVED, ahead.cookies)
        self.assertContains(self.client.get(self.home), "data-welcome")

    def test_a_stale_cookie_means_nothing_to_a_signed_out_page(self):
        self.client.cookies[ARRIVED] = "1"
        page = self.client.get(self.login)
        self.assertNotContains(page, "data-welcome")

    @override_settings(SESSION_COOKIE_SECURE=True)
    def test_the_cookie_is_secure_where_the_session_cookie_is(self):
        self.assertTrue(self.log_in().cookies[ARRIVED]["secure"])

    # The home-screen suggestion reads the same cookie, so only both switches off leave it unset.
    @override_settings(DOOR_MOTION=False, INSTALL_PROMPT=False)
    def test_the_switch_removes_it(self):
        self.assertNotIn(ARRIVED, self.log_in().cookies)
        self.client.cookies[ARRIVED] = "1"
        self.assertNotContains(self.client.get(self.home), "data-welcome")


class LaunchArrivalTests(TestCase):
    """The arrival also plays on a new window's first page: the installed app just started, or a new tab.
    The browser decides that (templates/base.html); the server only sends the script to a signed-in page."""

    SCRIPT = 'sessionStorage'

    def setUp(self):
        _, self.host = make_group(group_name="Kamuning Card Club")
        self.home = reverse("home")

    def test_a_signed_in_page_carries_the_script_in_the_head(self):
        self.client.force_login(self.host.user)
        page = self.client.get(self.home).content.decode()
        head, body = page.split("</head>", 1)
        # In the head, so the mark is on <html> before the first paint; no script is in the body (ScriptsLoadOnceTests).
        script = head.split("<script>(function(r){", 1)[1].split("</script>", 1)[0]
        self.assertIn('"pn-launched"', script)
        self.assertIn("r.dataset.launch", script)
        self.assertNotIn("<script", body)
        # Nothing in the head but tags: stray text there (a {# #} comment over several lines) ends the head early,
        # and the stylesheet after it loses the screen-change opt-in.
        text = re.sub(r"<(script|title)\b.*?</\1>|<[^>]+>", "", head.split("<head>", 1)[1], flags=re.S)
        self.assertEqual(text.strip(), "")
        self.assertIn('n.type==="navigate"', script)
        # The server marks nothing by itself: a later visit is not an arrival.
        self.assertNotIn("data-welcome", page)

    def test_a_signed_out_page_has_no_script(self):
        self.assertNotContains(self.client.get(reverse("login")), self.SCRIPT)

    def test_a_front_door_screen_seen_signed_in_leaves_it_for_the_page_behind_it(self):
        _, token = services.create_invite(make_group(host_name="rosa", group_name="Other Club")[1])
        self.client.force_login(self.host.user)
        self.assertNotContains(self.client.get(reverse("invite_accept", args=[token])), self.SCRIPT)

    @override_settings(LAUNCH_ARRIVAL=False)
    def test_its_switch_removes_it_and_leaves_the_login_arrival(self):
        self.client.force_login(self.host.user)
        self.assertNotContains(self.client.get(self.home), self.SCRIPT)
        self.client.logout()
        self.client.post(reverse("login"), {"username": "hana", "password": "tablestakes-91"})
        self.assertContains(self.client.get(self.home), "data-welcome")

    @override_settings(DOOR_MOTION=False)
    def test_the_front_door_switch_removes_it_too(self):
        self.client.force_login(self.host.user)
        self.assertNotContains(self.client.get(self.home), self.SCRIPT)
