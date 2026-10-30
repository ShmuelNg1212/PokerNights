"""Fixture for the seat draw. Run alone on a fresh temporary SQLite database.

Three open sets of one group: six players (Ben and Cara have logins), two players, and twelve.
"""
import json, uuid
from django.contrib.auth import get_user_model
from django.utils import timezone
from games import services as games
from groups import services as groups
from groups.models import Member
User = get_user_model()
hana = User.objects.create_user("hana", password="tablestakes-91")
host = groups.create_group(hana, "Kamuning Card Club")
login = lambda name: Member.objects.create(group=host.group, user=User.objects.create_user(name.lower(), password="tablestakes-91"), display_name=name)
ben, cara = login("Ben"), login("Cara")
def table(name, seats, members):
    t = games.create_table(host, name, seats)
    s = games.create_session(host, {"table_id": t.pk, "game_date": timezone.localdate(), "location": "Carlo's garage", "game_type": "nlh",
        "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 500000, "default_buy_in": 100000})
    games.transition(s.pk, host, "open")
    games.add_participants(s.pk, host, [m.pk for m in members], uuid.uuid4())
    return s
roster = lambda names: [groups.add_roster_player(host, n) for n in names]
four = roster(["Miguel", "Carlo", "Trina", "Paolo"])
six = table("Garage table", 9, [ben, cara] + four)
two = table("Kitchen table", 6, [ben] + roster(["Jerome"]))
twelve = table("Long table", 12, [ben, cara] + four + roster(["Bea", "Anton", "Maria Clara de los Santos", "Jun", "Isko", "Nonoy"]))
late = groups.add_roster_player(host, "Latecomer")
manifest = {"six": six.pk, "two": two.pk, "twelve": twelve.pk, "late": late.pk}
open("/private/tmp/pn-seat-draw-manifest.json", "w").write(json.dumps(manifest))
print("SEAT_DRAW_IDS", manifest)
