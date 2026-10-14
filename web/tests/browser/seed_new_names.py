"""Fixture for new_names.mjs. Run after seed.py on a fresh temporary SQLite database.

An open set at a 12-seat table with Miguel seated, and a removed roster player named Gone.
Writes the set's id to /private/tmp/pn-new-names-manifest.json.
"""
import datetime
import json
import uuid

from games import services as games
from groups import services as groups
from groups.models import Member

host = Member.objects.get(user__username="hana", group__name="Kamuning Card Club")
table = games.create_table(host, "Big table", 12)
session = games.create_session(host, {"table_id": table.pk, "game_date": datetime.date(2026, 10, 14), "location": "", "game_type": "nlh",
                                      "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 200000, "default_buy_in": 100000})
games.transition(session.pk, host, "open")
games.add_participants(session.pk, host, [Member.objects.get(group=host.group, display_name="Miguel").pk], uuid.uuid4())
groups.remove_member(host, groups.add_roster_player(host, "Gone").pk)
with open("/private/tmp/pn-new-names-manifest.json", "w") as out:
    json.dump({"set": session.pk}, out)
print("NEW NAMES SET", session.pk)
