"""The site header (2026-10-17): the brand on Your groups, the way back on every deeper page, and the
account token whose panel holds the username and Log out."""

from django.test import TestCase, override_settings
from django.urls import reverse

from notify.tests.test_notices import Table

KEYS = {"PUSH_ALERTS": True, "VAPID_PUBLIC_KEY": "BPublicKey", "VAPID_PRIVATE_KEY": "private"}


class HeaderTests(TestCase):
    def setUp(self):
        self.table = Table()
        self.client.force_login(self.table.host.user)

    def parts(self, url):
        page = self.client.get(url).content.decode()
        header = page.split('<header class="site-header">')[1].split("</header>")[0]
        main = page.split('<main id="main"')[1]
        return header, main

    def test_your_groups_shows_the_brand_and_no_way_back(self):
        header, main = self.parts(reverse("home"))
        self.assertIn('class="brand"', header)
        self.assertNotIn("table-bar", header + main)

    def test_each_deeper_page_puts_its_way_back_in_the_header_instead_of_the_brand(self):
        session, group = self.table.session, self.table.group
        member = group.members.get(user=self.table.host.user)
        pages = {
            reverse("group", args=[group.pk]): ("/", "Your groups"),
            reverse("night", args=[session.night_id]): (f"/g/{group.pk}/", group.name),
            reverse("session", args=[session.pk]): (f"/n/{session.night_id}/", f'<span class="back-kind">Session: </span>{session.table.name}'),
        }
        pages[reverse("player", args=[group.pk, member.pk])] = (None, f"{group.name} stats")
        for url, (href, words) in pages.items():
            with self.subTest(url=url):
                header, main = self.parts(url)
                self.assertIn('<nav class="table-bar">', header)
                if href:
                    self.assertIn(f'<a href="{href}">', header)
                self.assertIn(words, header)
                self.assertNotIn('class="brand"', header)
                self.assertNotIn("table-bar", main)

    def test_the_set_page_keeps_its_live_status_in_the_header(self):
        header, main = self.parts(reverse("session", args=[self.table.session.pk]))
        self.assertIn('<span id="live-status" class="live-status" aria-live="polite"></span>', header)
        self.assertNotIn("live-status", main)

    def test_the_session_status_moves_beside_the_heading(self):
        header, main = self.parts(reverse("night", args=[self.table.session.night_id]))
        self.assertNotIn("badge", header)
        self.assertIn('<span class="badge">Session ', main.split('data-carry="title"')[1])

    def test_the_account_token_holds_the_username_and_log_out(self):
        header, _ = self.parts(reverse("home"))
        user = self.table.host.user
        self.assertIn('<details id="account" class="account" data-turbo-permanent data-account>', header)
        self.assertIn(f'<span class="chip account-chip k{(user.pk - 1) % 10 + 1}" aria-hidden="true">{user.username[0].upper()}</span>', header)
        self.assertIn(f'<span class="visually-hidden">Account: {user.username}</span>', header)
        self.assertIn(f'<strong class="account-name">{user.username}</strong>', header)
        account = header.split('id="account"')[1]
        self.assertIn('action="/accounts/logout/"', account)
        self.assertIn("Log out", account)
        self.assertNotIn('class="who"', header)

    @override_settings(**KEYS)
    def test_the_bell_comes_before_the_account_token(self):
        header, _ = self.parts(reverse("home"))
        self.assertLess(header.index('id="alerts"'), header.index('id="account"'))

    def test_the_log_out_form_is_the_only_one_in_the_header(self):
        header, _ = self.parts(reverse("session", args=[self.table.session.pk]))
        self.assertEqual(header.count("<form"), 1)
