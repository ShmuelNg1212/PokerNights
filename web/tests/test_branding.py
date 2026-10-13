import os
import struct
from xml.etree import ElementTree

from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

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
