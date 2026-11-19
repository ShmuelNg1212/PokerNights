"""Fixture for the host dock before the start. Run alone on a fresh temporary SQLite database.

Host hana is not seated at any set. Joining sets: eight players of twelve seats (Join beside Players),
two of two (full, no Join), eleven players of twelve at 320px, and one more of twelve that the probe
joins. A draft with three players (ready to start). A set in play, where the host folds the dock.
"""
import json, uuid
from django.contrib.auth import get_user_model
from django.utils import timezone
from games import services as games
from groups import services as groups
User = get_user_model()
hana = User.objects.create_user("hana", password="tablestakes-91")
host = groups.create_group(hana, "Kamuning Card Club")
names = ["Ben", "Miguel", "Carlo", "Trina", "Paolo", "Bea", "Anton", "Maria Clara de los Santos", "Jun", "Isko", "Nonoy", "Lani"]
roster = [groups.add_roster_player(host, name) for name in names]


def table(name, count, seats, action="open"):
    t = games.create_table(host, name, seats)
    s = games.create_session(host, {"table_id": t.pk, "game_date": timezone.localdate(), "location": "Carlo's garage", "game_type": "nlh",
        "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 500000, "default_buy_in": 100000})
    if action in ("open", "start"):
        games.transition(s.pk, host, "open")
    games.add_participants(s.pk, host, [m.pk for m in roster[:count]], uuid.uuid4())
    if action == "start":
        games.transition(s.pk, host, "start", request_id=uuid.uuid4())
    return s.pk


manifest = {
    "eight": table("Garage table", 8, 12), "full": table("Kitchen table", 2, 2), "twelve": table("Long table", 11, 12),
    "join": table("Porch table", 4, 12), "draft": table("Draft table", 3, 6, action="setup"), "running": table("Play table", 4, 6, action="start"),
}
open("/private/tmp/pn-dock-start-manifest.json", "w").write(json.dumps(manifest))
print("DOCK_START_IDS", manifest)
