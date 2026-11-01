"""Isolated write fixtures for fluid.mjs. Run after seed.py on a fresh temporary DB."""
import json
import uuid
from pathlib import Path
from games import services as games
from games.tests.helpers import make_session
from groups.models import Member

host = Member.objects.get(user__username="hana", role="host")
roster = list(Member.objects.filter(group=host.group, status="active").order_by("pk"))
manifest = {}
for name in ("start", "reduced", "blocked", "checklist", "interrupt", "poll"):
    session = make_session(host, state="open" if name == "start" else "setup", table_name="Fluid " + name + " " + uuid.uuid4().hex[:6])
    players = [] if name in ("checklist", "interrupt", "poll") else games.add_participants(
        session.pk, host, [m.pk for m in roster[:2]], uuid.uuid4()
    )
    manifest[name] = {"set": session.pk, "players": [p.pk for p in players]}
Path("/private/tmp/pn-fluid-manifest.json").write_text(json.dumps(manifest))
print("FLUID", manifest)
