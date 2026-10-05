"""The pieces that let a phone install the site. No ledger page may ever be cached by them."""

import json
import struct

from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from groups.tests.helpers import make_group

STATIC = settings.BASE_DIR / "static"


class ManifestTests(TestCase):
    def setUp(self):
        self.manifest = json.loads((STATIC / "manifest.webmanifest").read_text())

    def test_required_members(self):
        m = self.manifest
        self.assertEqual((m["name"], m["short_name"], m["start_url"], m["scope"], m["display"]),
                         ("PokerNights", "PokerNights", "/", "/", "standalone"))
        self.assertIn("does not move money", m["description"])
        self.assertRegex(m["theme_color"], r"^#[0-9a-f]{6}$")
        self.assertRegex(m["background_color"], r"^#[0-9a-f]{6}$")

    def test_every_icon_exists_at_its_stated_size(self):
        sizes = {}
        for icon in self.manifest["icons"]:
            self.assertTrue(icon["src"].startswith("/static/icons/"))
            data = (STATIC / icon["src"].removeprefix("/static/")).read_bytes()
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            width, height = struct.unpack(">II", data[16:24])
            self.assertEqual(f"{width}x{height}", icon["sizes"])
            sizes[(icon["sizes"], icon["purpose"])] = True
        self.assertEqual(set(sizes), {("192x192", "any"), ("512x512", "any"), ("512x512", "maskable")})
        touch = (STATIC / "icons/app-180.png").read_bytes()
        self.assertEqual(struct.unpack(">II", touch[16:24]), (180, 180))


class InstallTagsTests(TestCase):
    TAGS = ['rel="manifest" href="/static/manifest.webmanifest"', 'rel="apple-touch-icon" href="/static/icons/app-180.png"',
            'name="apple-mobile-web-app-capable" content="yes"', 'name="mobile-web-app-capable" content="yes"',
            'name="apple-mobile-web-app-status-bar-style" content="black"', 'id="offline-notice"', "js/app.js", 'data-sw="on"']

    def test_tags_on_signed_out_and_signed_in_pages(self):
        group, host = make_group()
        signed_out = self.client.get(reverse("login"))
        self.client.force_login(host.user)
        for page in (signed_out, self.client.get(reverse("home")), self.client.get(reverse("group", args=[group.pk]))):
            for tag in self.TAGS:
                self.assertContains(page, tag)
            self.assertContains(page, 'id="offline-notice" class="offline-notice" role="status" data-turbo-permanent hidden')
            self.assertContains(page, '<body data-method="GET">')

    def test_a_page_rendered_from_a_post_says_so(self):
        page = self.client.post(reverse("login"), {"username": "nobody", "password": "x"})
        self.assertContains(page, '<body data-method="POST">')  # the refresh-on-return never reloads this


class ServiceWorkerTests(TestCase):
    def test_worker_needs_no_login_and_is_never_cached_for_long(self):
        response = self.client.get("/sw.js")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/javascript; charset=utf-8")
        self.assertEqual(response["Cache-Control"], "no-cache")

    def test_worker_caches_the_offline_page_and_nothing_else(self):
        body = self.client.get("/sw.js").content.decode()
        self.assertIn('const OFFLINE = "/offline/";', body)
        self.assertEqual(body.count("cache.add("), 1)
        self.assertNotIn("cache.put(", body)
        self.assertNotIn("addAll(", body)
        self.assertIn('event.request.mode !== "navigate"', body)  # only page navigations are touched
        self.assertIn("fetch(event.request).catch(", body)  # the network always comes first

    @override_settings(SERVICE_WORKER=False)
    def test_kill_switch_serves_a_worker_that_removes_itself(self):
        body = self.client.get("/sw.js").content.decode()
        self.assertIn("self.registration.unregister()", body)
        self.assertIn("caches.delete(key)", body)
        self.assertNotIn("cache.add(", body)
        self.assertNotIn('addEventListener("fetch"', body)
        self.assertNotContains(self.client.get(reverse("login")), 'data-sw="on"')

    def test_offline_page_is_self_contained_and_holds_no_data(self):
        group, host = make_group()
        self.client.force_login(host.user)
        signed_in = self.client.get("/offline/").content.decode()
        self.client.logout()
        signed_out = self.client.get("/offline/")
        self.assertEqual(signed_out.status_code, 200)
        html = signed_out.content.decode()
        self.assertEqual(html, signed_in)  # nothing about the viewer is in it
        for outside in ("/static/", 'rel="stylesheet"', "<script src", "<img", "csrfmiddlewaretoken", host.user.username, group.name):
            self.assertNotIn(outside, html)
        self.assertIn("You're offline", html)
        self.assertIn("Try again", html)
