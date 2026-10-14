import json
import os
import re
import struct
import zlib
from xml.etree import ElementTree

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

from config.pwa import SPLASH_SIZES, splash_file
from groups import services as groups
from groups.tests.helpers import make_group

LOGOS = ["logo-mark.svg", "logo-horizontal.svg", "app-icon.svg", "logo-mono.svg"]


class BrandingTests(TestCase):
    def test_each_logo_is_a_self_contained_svg(self):
        for name in LOGOS:
            with self.subTest(name=name):
                path = finders.find(f"branding/{name}")
                self.assertIsNotNone(path)
                root = ElementTree.parse(path).getroot()
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                self.assertEqual(root.get("aria-label"), "PokerNights")
                markup = open(path).read()
                # No raster images, outside files or text that needs an installed font.
                for banned in ("<image", "<text", "href=", "url("):
                    self.assertNotIn(banned, markup)

    def test_header_and_favicon_use_the_mark_with_one_accessible_name(self):
        _, host = make_group()
        self.client.force_login(host.user)
        page = self.client.get(reverse("home")).content.decode()
        self.assertIn('<link rel="icon" type="image/svg+xml" href="/static/branding/logo-mark.svg">', page)
        brand = page.split('<a class="brand"')[1].split("</a>")[0]
        self.assertIn('src="/static/branding/logo-mark.svg" alt=""', brand)
        self.assertTrue(brand.endswith("PokerNights"))


class LinkPreviewTests(TestCase):
    """The card a chat app shows for a pasted link. The pages are fetched logged out, as a chat app fetches them."""

    CARD = [
        '<meta property="og:title" content="PokerNights">',
        '<meta property="og:description" content="Records buy-ins and cash-outs for a home poker game and works out who pays whom. It does not move money.">',
        '<meta property="og:image" content="http://testserver/static/branding/link-preview.png">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        '<meta name="twitter:card" content="summary_large_image">',
    ]

    def assert_card(self, page):
        for tag in self.CARD:
            self.assertIn(tag, page)
        # An invite, reset or claim address contains its token, so the page does not repeat its address.
        self.assertNotIn("og:url", page)

    def test_the_home_address_leads_to_a_page_with_the_card(self):
        self.assert_card(self.client.get(reverse("home"), follow=True).content.decode())

    def test_an_invite_link_shows_the_same_card_and_names_no_group(self):
        _, host = make_group(group_name="Kamuning Card Club")
        _, token = groups.create_invite(host)
        page = self.client.get(reverse("invite_accept", args=[token]), follow=True).content.decode()
        self.assert_card(page)
        head = page.split("</head>")[0]
        self.assertNotIn("Kamuning", head)
        self.assertNotIn(token, head)

    def test_the_picture_is_the_size_chat_apps_expect(self):
        path = finders.find("branding/link-preview.png")
        self.assertIsNotNone(path)
        with open(path, "rb") as picture:
            header = picture.read(24)
        self.assertEqual(header[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", header[16:24]), (1200, 630))
        # WhatsApp has dropped larger pictures.
        self.assertLess(os.path.getsize(path), 300_000)


def png_size(path):
    with open(path, "rb") as picture:
        header = picture.read(24)
    assert header[:8] == b"\x89PNG\r\n\x1a\n", path
    return struct.unpack(">II", header[16:24])


def first_pixel_alpha(path):
    """The top-left pixel's alpha, for an 8-bit RGBA PNG. Every row filter leaves a row's first pixel as stored."""
    with open(path, "rb") as picture:
        data = picture.read()
    position, compressed, colour_type = 8, b"", None
    while position < len(data):
        length, kind = struct.unpack(">I4s", data[position:position + 8])
        chunk = data[position + 8:position + 8 + length]
        if kind == b"IHDR":
            colour_type = chunk[9]
        elif kind == b"IDAT":
            compressed += chunk
        position += 12 + length
    assert colour_type == 6, "not RGBA"
    return zlib.decompress(compressed)[4]


class LaunchScreenTests(TestCase):
    """The installed app's launch: an image per iPhone screen, and clear-ground icons for Android's."""

    def test_every_page_names_a_launch_screen_for_each_iphone(self):
        page = self.client.get(reverse("login")).content.decode()
        tags = re.findall(r'<link rel="apple-touch-startup-image" media="([^"]+)" href="([^"]+)">', page)
        self.assertEqual(len(tags), len(SPLASH_SIZES))
        for (media, href), (width, height, ratio) in zip(tags, SPLASH_SIZES):
            self.assertEqual(media, f"(device-width: {width}px) and (device-height: {height}px) and (-webkit-device-pixel-ratio: {ratio}) and (orientation: portrait)")
            self.assertEqual(href, f"/static/{splash_file(width, height, ratio)}")

    def test_each_image_fills_its_screen_exactly(self):
        # An iPhone skips an image that is not its exact size; it does not stretch one.
        for width, height, ratio in SPLASH_SIZES:
            path = finders.find(splash_file(width, height, ratio))
            self.assertIsNotNone(path, (width, height, ratio))
            self.assertEqual(png_size(path), (width * ratio, height * ratio))
            self.assertLess(os.path.getsize(path), 60_000)

    def test_the_renderer_draws_the_same_sizes(self):
        script = open(os.path.join(settings.BASE_DIR, "web/tests/browser/make_splash.mjs")).read()
        listed = re.search(r"const SIZES=\[(.*?)\];", script).group(1)
        self.assertEqual(tuple(tuple(map(int, size)) for size in re.findall(r"\[(\d+),(\d+),(\d+)\]", listed)), SPLASH_SIZES)

    def test_android_draws_its_launch_from_a_clear_ground_icon(self):
        manifest = json.load(open(finders.find("manifest.webmanifest")))
        self.assertEqual(manifest["background_color"], "#130e0a")
        icons = {icon["purpose"] + " " + icon["sizes"]: icon["src"] for icon in manifest["icons"]}
        self.assertEqual(icons, {
            "any 192x192": "/static/icons/app-any-192.png",
            "any 512x512": "/static/icons/app-any-512.png",
            "maskable 512x512": "/static/icons/app-maskable-512.png",
        })
        for name, size in [("app-any-192.png", 192), ("app-any-512.png", 512)]:
            path = finders.find("icons/" + name)
            self.assertEqual(png_size(path), (size, size))
            self.assertEqual(first_pixel_alpha(path), 0)
