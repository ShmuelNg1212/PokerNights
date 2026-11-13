"""Fixture for chip_pot.mjs (a chip to the pot). Run alone on a fresh temporary SQLite database.

Running sets of one group, each with ₱1,000 bought in by each player: six players (the story, with Ben's phone
watching), twelve (320px, rows under the dock), six at 1280px, and four each for reduced motion, a blocked
Motion file, a slowed processor and a hidden tab. One open set with buy-ins waits to be started.
"""
import json, os, uuid
from django.contrib.auth import get_user_model
from django.utils import timezone
from games import services as games
from groups import services as groups
from groups.models import Member
from ledger import services as ledger
User = get_user_model()
hana = User.objects.create_user("hana", password="tablestakes-91")
host = groups.create_group(hana, "Kamuning Card Club")
ben = Member.objects.create(group=host.group, user=User.objects.create_user("ben", password="tablestakes-91"), display_name="Ben")
names = ["Miguel", "Carlo", "Trina", "Paolo", "Bea", "Anton", "Maria Clara de los Santos", "Jun", "Isko", "Nonoy", "Lani"]
roster = [groups.add_roster_player(host, name) for name in names]
manifest = {}


def table(key, count, start=True):
    t = games.create_table(host, "Chip " + key, max(count, 2))
    s = games.create_session(host, {"table_id": t.pk, "game_date": timezone.localdate(), "location": "Carlo's garage", "game_type": "nlh",
        "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 500000, "default_buy_in": 100000})
    games.transition(s.pk, host, "open")
    players = games.add_participants(s.pk, host, [ben.pk] + [m.pk for m in roster[:count - 1]], uuid.uuid4())
    for p in players:
        ledger.record_buy_in(s.pk, host, p.pk, 100000, uuid.uuid4())
    if start:
        games.transition(s.pk, host, "start", opening_buy_ins=False)
    manifest[key] = {"set": s.pk, "players": [p.pk for p in players]}


table("main", 6)
table("small", 12)
table("desk", 6)
for key in ("still", "plain", "slow", "hidden"):
    table(key, 4)
table("start", 4, start=False)
path = os.environ.get("PN_MANIFEST", "/private/tmp/pn-chip-pot-manifest.json")
with open(path, "w") as out:
    json.dump(manifest, out)
print("CHIP_POT", manifest)
