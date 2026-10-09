"""Which forms update in place (Turbo, forms only) and which still load a page. Behaviour is in inplace.mjs."""

import re

from django.test import TestCase, override_settings
from django.urls import reverse

from ledger.tests.helpers import Night
from settlement.tests.test_archive import closed_example

IN_PLACE = ("buyins/add", "cashouts/add", "/transition/", "/counts/confirm/", "/finalize/", "/reverse/", "/withdraw/", "/paid/", "/unpaid/")
ELSEWHERE = ("/close/", "/next-set/", "/logout/", "/archive/", "/delete/")


def forms(page):
    return re.findall(r"<form\b[^>]*>", page.content.decode())


class InPlaceMarksTests(TestCase):
    def setUp(self):
        self.night = Night("A", "B")
        self.night.buy("A", 1000)
        self.client.force_login(self.night.host.user)

    def marked(self, page):
        return [f for f in forms(page) if 'data-turbo="true"' in f]

    def test_set_page_forms_are_marked_and_carry_the_page_settings(self):
        page = self.client.get(reverse("session", args=[self.night.session.pk]))
        post = [f for f in forms(page) if 'method="post"' in f and "/logout/" not in f]
        self.assertTrue(post)
        self.assertEqual(self.marked(page), post)  # every form on the set page returns to the set page
        self.assertContains(page, '<meta name="turbo-refresh-method" content="morph">')
        self.assertContains(page, '<meta name="turbo-refresh-scroll" content="preserve">')
        self.assertContains(page, '<div id="table-sheets" data-turbo-permanent></div>')

    def test_count_up_buttons_outside_their_form_are_marked(self):
        self.night.go("reconciliation")
        page = self.client.get(reverse("session", args=[self.night.session.pk]))
        buttons = re.findall(r'<button[^>]*form="counts-form"[^>]*>', page.content.decode())
        self.assertTrue(buttons)
        self.assertTrue(all('data-turbo="true"' in b for b in buttons))  # Turbo checks the pressed button too

    def test_session_page_marks_paid_and_undo_only(self):
        night = closed_example()
        self.client.force_login(night.host.user)
        page = self.client.get(reverse("night", args=[night.session.night_id]))
        marked = self.marked(page)
        self.assertTrue(marked)
        self.assertTrue(all("/paid/" in f or "/unpaid/" in f for f in marked))
        self.assertContains(page, 'content="morph"')

    def test_other_pages_have_no_marked_form_and_no_morph_setting(self):
        group = self.night.group
        open_night = reverse("night", args=[self.night.session.night_id])
        for url in (reverse("home"), reverse("group", args=[group.pk]), reverse("group", args=[group.pk]) + "?view=settings",
                    reverse("session_create", args=[group.pk]), reverse("login")):
            page = self.client.get(url, follow=True)
            self.assertEqual(self.marked(page), [], url)
            self.assertNotContains(page, "turbo-refresh-method")
        for f in forms(self.client.get(open_night)):
            if any(part in f for part in ELSEWHERE):
                self.assertNotIn("data-turbo", f)

    def test_every_page_switches_the_page_cache_off_and_loads_the_pinned_library(self):
        for url in (reverse("login"), reverse("home"), reverse("session", args=[self.night.session.pk])):
            page = self.client.get(url, follow=True)
            self.assertContains(page, '<meta name="turbo-cache-control" content="no-cache">')
            self.assertContains(page, "js/vendor/turbo-8.0.23.js")
            self.assertContains(page, "js/turbo-setup.js")

    @override_settings(STATIC_VERSION="abc1234567")
    def test_the_library_address_does_not_change_with_a_release(self):
        html = self.client.get(reverse("login")).content.decode()
        self.assertIn('src="/static/js/vendor/turbo-8.0.23.js"', html)
        self.assertIn('src="/static/js/turbo-setup.js?v=abc1234567"', html)
        self.assertIn('src="/static/js/vendor/motion-14.0.0.js"', html)
        self.assertIn('src="/static/js/motion.js?v=abc1234567"', html)


class ScriptsLoadOnceTests(TestCase):
    """Every page script loads from the head of every page, so a screen change never runs one twice."""

    NAMES = ("page", "app", "vendor/turbo-8.0.23", "turbo-setup",
             "vendor/motion-14.0.0", "motion", "forms", "toasts", "changes", "flow", "sheets", "numpad", "live",
             "clock", "counts", "dock", "pick", "password", "copy", "roster", "stats", "perf")

    def test_scripts_are_in_the_head_in_order_and_none_in_the_body(self):
        night = Night("A")
        self.client.force_login(night.host.user)
        for url in (reverse("login"), reverse("home"), reverse("session", args=[night.session.pk]),
                    reverse("night", args=[night.session.night_id])):
            html = self.client.get(url, follow=True).content.decode()
            head, body = html.split("</head>", 1)
            found = re.findall(r'<script src="/static/js/([^"?]+)\.js[^"]*" defer data-turbo-track="reload"></script>', head)
            self.assertEqual(tuple(found), self.NAMES, url)
            self.assertNotIn("<script", body, url)
            # The address carries ?v=<release> on Vercel, where the build runs these tests.
            self.assertRegex(head, r'rel="stylesheet" href="/static/css/app\.css[^"]*" data-turbo-track="reload"')
