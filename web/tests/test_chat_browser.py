"""The card that asks a person in a chat app's browser to open the front door in Safari or Chrome."""

from urllib.parse import quote

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from config.chat_browser import HERE_COOKIE, detect
from groups import services
from groups.tests.helpers import make_group, make_user

CARD = 'id="chat-browser"'

# Real user agents, as the apps sent them in 2024–2026.
IPHONE = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
ANDROID = "Mozilla/5.0 (Linux; Android 14; SM-S918B Build/UP1A.231005.007; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/125.0.6422.165 Mobile Safari/537.36"
AGENTS = {
    "messenger-ios": (IPHONE + " [FBAN/MessengerForiOS;FBAV/460.0.0.37.106;FBBV/617468937;FBDV/iPhone15,2;FBMD/iPhone;FBSN/iOS;FBSV/17.5;FBSS/3;FBCR/;FBID/phone;FBLC/en_US;FBOP/5]", "ios", "Messenger"),
    "messenger-lite-ios": (IPHONE + " [FBAN/MessengerLiteForiOS;FBAV/460.0.0;FBDV/iPhone15,2]", "ios", "Messenger"),
    "messenger-android": (ANDROID + " [FB_IAB/MESSENGER;FBAV/460.0.0.48.109;]", "android", "Messenger"),
    "facebook-ios": (IPHONE + " [FBAN/FBIOS;FBAV/470.0.0.40.98;FBBV/628431213;FBDV/iPhone15,2;FBMD/iPhone;FBSN/iOS;FBSV/17.5;FBSS/3;FBCR/;FBID/phone;FBLC/en_US;FBOP/80]", "ios", "Facebook"),
    "facebook-android": (ANDROID + " [FB_IAB/FB4A;FBAV/470.0.0.43.109;]", "android", "Facebook"),
    "instagram-ios": (IPHONE + " Instagram 334.0.4.32.98 (iPhone15,2; iOS 17_5; en_US; en; scale=3.00; 1179x2556; 607420089)", "ios", "Instagram"),
    "instagram-android": (ANDROID + " Instagram 337.0.0.35.102 Android (34/14; 420dpi; 1080x2400; samsung; SM-S918B; dm3q; qcom; en_US; 614250530)", "android", "Instagram"),
    "viber-android": (ANDROID + " Viber/22.1.0.0", "android", "Viber"),
    "viber-ios": (IPHONE + " Viber/22.1.0", "ios", "Viber"),
    "line-ios": (IPHONE + " Safari Line/14.10.0", "line", "LINE"),
    "line-android": (ANDROID + " Line/14.10.0/IAB", "line", "LINE"),
    "wechat-ios": (IPHONE + " MicroMessenger/8.0.49(0x18003133) NetType/WIFI Language/en", "ios", "WeChat"),
}
BROWSERS = {
    "safari": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "chrome-android": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
    "samsung": "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/25.0 Chrome/121.0.0.0 Mobile Safari/537.36",
    "chrome-iphone": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/126.0.6478.54 Mobile/15E148 Safari/604.1",
    "desktop": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}
MESSENGER_IOS = AGENTS["messenger-ios"][0]
MESSENGER_ANDROID = AGENTS["messenger-android"][0]


class DetectTests(SimpleTestCase):
    def test_each_chat_app_and_phone(self):
        for name, (agent, kind, app) in AGENTS.items():
            with self.subTest(name):
                self.assertEqual(detect(agent), (kind, app))

    def test_browsers_are_left_alone(self):
        for name, agent in BROWSERS.items():
            with self.subTest(name):
                self.assertEqual(detect(agent), (None, ""))
        self.assertEqual(detect(""), (None, ""))

    def test_a_chat_marker_on_a_computer_is_left_alone(self):
        self.assertEqual(detect(BROWSERS["desktop"] + " Viber/22.1"), (None, ""))


class CardTests(TestCase):
    def setUp(self):
        _, self.host = make_group()
        self.token = services.create_invite(self.host)[1]
        self.join = reverse("invite_accept", args=[self.token])

    def get(self, path, agent=MESSENGER_IOS, **kwargs):
        return self.client.get(path, headers={"User-Agent": agent}, **kwargs)

    def signup_path(self):
        return f"{reverse('signup')}?next={quote(self.join, safe='')}"

    def test_an_invite_opened_in_messenger_shows_the_card_above_sign_up(self):
        page = self.get(self.join, follow=True)
        self.assertContains(page, CARD)
        self.assertContains(page, "Open this in Safari")
        self.assertContains(page, "Messenger’s browser")
        self.assertContains(page, "Your invite comes with you.")
        self.assertContains(page, "Continue here")
        body = page.content.decode()
        self.assertLess(body.index(CARD), body.index("<form"))

    def test_every_front_door_page_has_it(self):
        member = services.add_roster_player(self.host, "Ben")
        claim = services.create_claim_link(self.host, member.id)[2]
        ben = make_user("ben")
        services.accept_invite(ben, services.create_invite(self.host)[1])
        reset = services.create_password_reset(self.host, ben.memberships.get().id)[2]
        for path in (reverse("login"), self.signup_path(), reverse("claim", args=[claim]), reverse("password_reset", args=[reset])):
            with self.subTest(path):
                self.assertContains(self.get(path, follow=True), CARD)

    def test_not_on_a_dead_link_or_the_invite_needed_page(self):
        self.assertNotContains(self.get(reverse("invite_accept", args=["nope"])), CARD, status_code=404)
        with self.settings(SIGNUP_REQUIRES_INVITE=True):
            self.assertNotContains(self.get(reverse("signup")), CARD, status_code=403)

    def test_not_in_a_browser(self):
        for name, agent in BROWSERS.items():
            with self.subTest(name):
                self.assertNotContains(self.get(self.signup_path(), agent), CARD)

    def test_not_inside_the_app(self):
        self.client.force_login(self.host.user)
        self.assertNotContains(self.get(reverse("home")), CARD)

    def test_android_offers_chrome_with_this_exact_address(self):
        page = self.get(self.signup_path(), MESSENGER_ANDROID)
        self.assertContains(page, "Open this in Chrome")
        address = "testserver" + self.signup_path()
        intent = f"intent://{address}#Intent;scheme=http;package=com.android.chrome;S.browser_fallback_url={quote('http://' + address, safe='')};end"
        self.assertContains(page, f'href="{intent}"'.replace("&", "&amp;"))
        self.assertContains(page, 'data-turbo="false"')

    def test_line_opens_its_own_way_out(self):
        page = self.get(self.signup_path(), AGENTS["line-android"][0])
        self.assertContains(page, "Open in browser")
        self.assertContains(page, ("http://testserver" + self.signup_path() + "&openExternalBrowser=1").replace("&", "&amp;"))
        page = self.get(reverse("login"), AGENTS["line-ios"][0])
        self.assertContains(page, "http://testserver/accounts/login/?openExternalBrowser=1")

    def test_iphone_has_no_button_that_cannot_work(self):
        page = self.get(self.signup_path())
        self.assertNotContains(page, "intent://")
        self.assertNotContains(page, "openExternalBrowser")
        self.assertContains(page, "Open in Safari")

    def test_copy_link_carries_the_whole_address(self):
        page = self.get(self.signup_path())
        self.assertContains(page, ('data-chat-copy="http://testserver' + self.signup_path() + '"').replace("&", "&amp;"))

    def test_continue_here_without_javascript_drops_the_card_for_the_browser_session(self):
        page = self.get(self.signup_path())
        self.assertContains(page, (self.signup_path() + "&amp;here=1"))
        gone = self.get(self.signup_path() + "&here=1")
        self.assertNotContains(gone, CARD)
        self.assertEqual(gone.cookies[HERE_COOKIE].value, "1")
        self.assertEqual(gone.cookies[HERE_COOKIE]["max-age"], "")
        self.assertNotContains(self.get(reverse("login")), CARD)

    def test_the_invite_alone_says_so(self):
        self.assertNotContains(self.get(reverse("login")), "comes with you")

    def test_front_door_answers_vary_by_user_agent(self):
        self.assertIn("User-Agent", self.get(self.signup_path())["Vary"])
        self.assertIn("User-Agent", self.get(self.signup_path(), BROWSERS["safari"])["Vary"])

    @override_settings(CHAT_BROWSER_CARD=False)
    def test_switch_off(self):
        self.assertNotContains(self.get(self.signup_path()), CARD)


class InstallSheetTests(TestCase):
    """The home-screen sheet after login learns the chat browser from the server, not its own list."""

    def test_the_page_says_which_chat_browser(self):
        _, host = make_group()
        self.client.force_login(host.user)
        page = self.client.get(reverse("home"), headers={"User-Agent": MESSENGER_ANDROID})
        self.assertContains(page, 'data-chat-browser="android"')
        page = self.client.get(reverse("home"), headers={"User-Agent": BROWSERS["safari"]})
        self.assertNotContains(page, "data-chat-browser")

    @override_settings(CHAT_BROWSER_CARD=False)
    def test_the_switch_leaves_the_install_sheet_its_knowledge(self):
        _, host = make_group()
        self.client.force_login(host.user)
        self.assertContains(self.client.get(reverse("home"), headers={"User-Agent": MESSENGER_ANDROID}), 'data-chat-browser="android"')


class FocusTests(TestCase):
    """Focus scrolls a short phone past the card, so the first field waits while the card leads."""

    def test_the_first_field_waits_while_the_card_shows(self):
        self.assertNotContains(self.client.get(reverse("login"), headers={"User-Agent": MESSENGER_IOS}), "autofocus")
        self.assertContains(self.client.get(reverse("login"), headers={"User-Agent": BROWSERS["safari"]}), "autofocus")

    def test_a_refused_form_still_takes_the_refused_field(self):
        page = self.client.post(reverse("login"), {"username": "nobody", "password": "x"}, headers={"User-Agent": MESSENGER_IOS})
        self.assertContains(page, CARD)
        self.assertContains(page, "autofocus")


class WorkerTests(TestCase):
    def test_the_service_worker_leaves_the_front_door_to_the_browser(self):
        """A request the worker makes carries its own user agent, so the server could not see the chat app."""
        body = self.client.get("/sw.js").content.decode()
        self.assertIn("const FRONT_DOOR = /^\\/(accounts|join|claim)\\//;", body)
        self.assertIn('event.request.mode !== "navigate" || FRONT_DOOR.test(new URL(event.request.url).pathname)', body)
