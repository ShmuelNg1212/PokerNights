"""Static file addresses that change with each release, so browsers can cache them for a year."""

from django.conf import settings
from django.contrib.staticfiles.storage import StaticFilesStorage

# Only these are versioned. A font or image keeps one address, because the stylesheet
# refers to the font by a plain relative path and both references must match.
VERSIONED = (".css", ".js")


class VersionedStaticStorage(StaticFilesStorage):
    """Appends ``?v=<release>`` to stylesheet and script addresses. Files on disk keep their names."""

    def url(self, name):
        address = super().url(name)
        version = getattr(settings, "STATIC_VERSION", "")
        # A vendored library carries its version in its file name and is not re-downloaded per release.
        if version and name.endswith(VERSIONED) and "/vendor/" not in name:
            return f"{address}?v={version}"
        return address
