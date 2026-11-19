"""Django's {# #} comment ends at the line end. A comment that spans lines shows as text on the page."""

import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase

OPEN_WITHOUT_CLOSE = re.compile(r"\{#(?:(?!#\}).)*$", re.MULTILINE)


class TemplateCommentTests(SimpleTestCase):
    def test_no_comment_spans_lines(self):
        root = Path(settings.BASE_DIR)
        leaks = []
        for path in sorted(root.glob("**/templates/**/*.html")):
            if ".venv" in path.parts or "node_modules" in path.parts:
                continue
            for number, line in enumerate(path.read_text().splitlines(), 1):
                if OPEN_WITHOUT_CLOSE.search(line):
                    leaks.append(f"{path.relative_to(root)}:{number}")
        self.assertEqual(leaks, [], "Use {% comment %} for a comment on more than one line.")
