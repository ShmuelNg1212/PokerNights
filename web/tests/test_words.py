"""The agreed words (2026-10-31): "Go to" for moving, "Joining" for the state, "In progress" for a session."""

import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from games.models import GameSession
from games.tests.helpers import make_session
from groups.tests.helpers import make_group

# "open" stays as a verb for a link, an app or a disclosure. These are the retired meanings.
RETIRED = re.compile(r">\s*Open (set|the table|session)\b|\b(is|still) open\b|Open for players|\bNot closed\b|>Open<", re.IGNORECASE)


class AgreedWordsTests(SimpleTestCase):
    def test_no_template_uses_a_retired_word(self):
        found = []
        for path in Path(settings.BASE_DIR, "templates").rglob("*.html"):
            for number, line in enumerate(path.read_text().splitlines(), 1):
                if "{#" not in line and RETIRED.search(line):
                    found.append(f"{path.name}:{number}")
        self.assertEqual(found, [])

    def test_the_set_state_is_called_joining(self):
        self.assertEqual(GameSession.STATE_WORDS["open"], "Joining")


class WordsOnThePageTests(TestCase):
    def test_a_joining_set_says_so_and_the_way_there_says_go_to(self):
        group, host = make_group()
        session = make_session(host, state="open")
        self.client.force_login(host.user)
        page = self.client.get(reverse("group", args=[group.pk]))
        self.assertContains(page, f"Set {session.set_number} · Joining")
        self.assertContains(self.client.get(reverse("night", args=[session.night_id])), f"Go to set {session.set_number}")
        self.assertContains(self.client.get(reverse("session", args=[session.pk])), "Let players join")
