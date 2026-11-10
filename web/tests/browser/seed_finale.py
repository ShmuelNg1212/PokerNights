"""Fixture for the session finale. Run alone on a fresh temporary SQLite database.

Sessions of one group with their only set finalized. One is left for the host to close (eight players, with
Ben's phone watching). The others are closed already, and each fresh browser sees its finale once: two players,
twelve (a full table), a tie for the top result, and a session where everyone is even. Ben has a login and plays in each.
"""
import json, uuid
from django.contrib.auth import get_user_model
from games import services as games
from games.tests.helpers import make_session
from groups import services as groups
from groups.models import Member
from ledger import services as ledger
from settlement import services as settlement
User = get_user_model()
hana = User.objects.create_user("hana", password="tablestakes-91")
host = groups.create_group(hana, "Kamuning Card Club")
ben = Member.objects.create(group=host.group, user=User.objects.create_user("ben", password="tablestakes-91"), display_name="Ben")
names = ["Miguel", "Carlo", "Trina", "Paolo", "Bea", "Anton", "Maria Clara de los Santos", "Jun", "Isko", "Nonoy", "Lani"]
roster = [groups.add_roster_player(host, name) for name in names]
u = uuid.uuid4


def final(name, nets, close=True):
    members = [ben] + roster[:len(nets) - 1]
    s = make_session(host, state="open", table_name=name, seat_count=max(len(nets), 2))
    ps = games.add_participants(s.pk, host, [m.pk for m in members], u())
    for p in ps: ledger.record_buy_in(s.pk, host, p.pk, 100000, u())
    games.transition(s.pk, host, "start")
    games.transition(s.pk, host, "end")
    for p, net in zip(ps, nets): ledger.record_cash_out(s.pk, host, p.pk, 100000 + net, u())
    settlement.finalize(s.pk, host)
    if close: settlement.close_night(s.night_id, host)
    return s.night_id


EIGHT = [30000, 90000, 10000, -10000, -20000, -30000, -30000, -40000]
manifest = {
    "ready": final("Garage table", EIGHT, close=False),
    "eight": final("Kitchen table", EIGHT),
    "two": final("Corner table", [-50000, 50000]),
    "twelve": final("Long table", [20000, 60000, 40000, 100000, 10000, 0, -10000, -20000, -30000, -40000, -50000, -80000]),
    "tied": final("Tied table", [40000, -30000, 40000, -50000]),
    "even": final("Even table", [0, 0, 0]),
}
open("/private/tmp/pn-finale-manifest.json", "w").write(json.dumps(manifest))
print("FINALE_IDS", manifest)
