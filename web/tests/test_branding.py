from xml.etree import ElementTree

from django.contrib.staticfiles import finders
from django.test import TestCase
from django.urls import reverse

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
