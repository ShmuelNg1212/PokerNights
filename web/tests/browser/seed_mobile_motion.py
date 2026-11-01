"""Synthetic completion fixtures for mobile_motion.mjs. Run after the shared browser seeds."""
import json
import uuid
from pathlib import Path

from games.tests.helpers import make_session
from groups.models import Member

host = Member.objects.get(user__username="hana", role="host")
manifest = {}
for engine in ("chromium", "webkit"):
    for mode in ("native", "fallback"):
        session = make_session(host, state="setup", table_name="Mobile " + uuid.uuid4().hex[:6])
        manifest[engine + " " + mode] = session.pk
Path("/private/tmp/pn-mobile-motion-manifest.json").write_text(json.dumps(manifest))
