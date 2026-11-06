"""Fixture for the set start overture. Run alone on a fresh temporary SQLite database.

Open sets of one group, each consumed by one start: eight players without a draw, six with a seated draw
whose dealer is the last to join, two (the tap skip), two (the key skip), twelve (320px), eight at 1280px, and three for reduced
motion, a blocked Motion file and a slowed processor. Ben has a login and sits at every table, so a player's phone can watch.
"""
import json, uuid
from django.contrib.auth import get_user_model
from django.utils import timezone
from games import services as games, seats
from games.models import GameSession
from groups import services as groups
from groups.models import Member
User = get_user_model()
hana = User.objects.create_user("hana", password="tablestakes-91")
host = groups.create_group(hana, "Kamuning Card Club")
ben = Member.objects.create(group=host.group, user=User.objects.create_user("ben", password="tablestakes-91"), display_name="Ben")
names = ["Miguel", "Carlo", "Trina", "Paolo", "Bea", "Anton", "Maria Clara de los Santos", "Jun", "Isko", "Nonoy", "Lani"]
roster = [groups.add_roster_player(host, name) for name in names]


def table(name, count, draw=False):
    t = games.create_table(host, name, max(count, 2))
    s = games.create_session(host, {"table_id": t.pk, "game_date": timezone.localdate(), "location": "Carlo's garage", "game_type": "nlh",
        "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 500000, "default_buy_in": 100000})
    games.transition(s.pk, host, "open")
    games.add_participants(s.pk, host, [ben.pk] + [m.pk for m in roster[:count - 1]], uuid.uuid4())
    if draw:
        # The dealer is the last player to join: under the host dock at 390px, on the screen at 1280px.
        # The draw is random, so draw again until it falls that way, as a host may before the start.
        session = GameSession.objects.get(pk=s.pk)
        last = max(session.participants.all(), key=lambda p: p.join_order)
        for _ in range(200):
            games.draw_seats(s.pk, host, uuid.uuid4())
            if seats.seating(session).seats[0].participant.pk == last.pk:
                break
        games.choose_seat(s.pk, host, 2, uuid.uuid4())
    return s.pk


manifest = {
    "eight": table("Garage table", 8), "drawn": table("Drawn table", 6, draw=True), "two": table("Kitchen table", 2),
    "twelve": table("Long table", 12), "wide": table("Wide table", 8), "calm": table("Calm table", 4),
    "blocked": table("Blocked table", 4), "slow": table("Slow table", 8), "keys": table("Key table", 2),
}
open("/private/tmp/pn-overture-manifest.json", "w").write(json.dumps(manifest))
print("OVERTURE_IDS", manifest)
