"""Static file addresses that change when the file changes, so browsers can cache them for a year."""

import functools
import hashlib

from django.conf import settings
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import StaticFilesStorage

# Only these are versioned. A font or image keeps one address, because the stylesheet
# refers to the font by a plain relative path and both references must match.
VERSIONED = (".css", ".js")


@functools.lru_cache(maxsize=None)
def content_tag(name):
    """The first ten hex characters of the SHA-256 of the file, or None if it cannot be read.

    Read once for each process: a release is a new process, and a file does not change inside one.
    """
    try:
        path = finders.find(name)
        if not path:
            return None
        with open(path, "rb") as file:
            return hashlib.sha256(file.read()).hexdigest()[:10]
    except OSError:
        return None


class VersionedStaticStorage(StaticFilesStorage):
    """Appends ``?v=<tag of the file>`` to stylesheet and script addresses. Files on disk keep their names.

    A file that a release did not change keeps its address, and a phone keeps its copy.
    ``STATIC_VERSION`` (set only on Vercel) switches this on. It is also the tag for a file
    that cannot be read, so a fault here gives the address of a release, as before 2026-11-14.
    """

    def url(self, name):
        address = super().url(name)
        version = getattr(settings, "STATIC_VERSION", "")
        # A vendored library carries its version in its file name and is not re-downloaded per release.
        if version and name.endswith(VERSIONED) and "/vendor/" not in name:
            return f"{address}?v={content_tag(name) or version}"
        return address
