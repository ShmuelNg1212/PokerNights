"""Synthetic fixture for home.mjs (the Your groups page). Run alone on a fresh temporary database.

The viewer "mara" belongs to five groups in different states; "pia" hosts one of them and sees one card.
"""
import datetime
import json
import uuid
from pathlib import Path

from games import services as games
from games.tests.helpers import make_session, make_table
from groups import services as groups
from groups.models import Member
from groups.tests.helpers import make_group, make_user
from ledger import services as ledger
from settlement.tests.test_stats import Club

u = uuid.uuid4
mara = make_user("mara")
day = lambda n: datetime.date(2026, 10, 1) + datetime.timedelta(days=n)

def club(host_name, name):
    c = Club.__new__(Club)
    c.group, c.host = make_group(host_name, name)
    c.table = make_table(c.host)
    c.members = {}
    return c

def join(c, role="player"):
    m = c.member("Mara")
    Member.objects.filter(pk=m.pk).update(user=mara, role=role)
    return Member.objects.get(pk=m.pk)

# 1. A set in play, more open sessions, fourteen players, dues, records in pesos and chips. Mara is a host here.
one = club("hana", "Kamuning Card Club")
me = join(one, "host")
for name in ["Miguel", "Carlo", "Trina", "Paolo", "Jerome", "Bea", "Anton", "Ben", "Luz", "Rico", "Sam", "Tess"]:
    one.member(name)
one.session(day(0), {"Mara": (1000, 2450), "Miguel": (1000, 0), "Carlo": (1450, 1000)})
one.session(day(1), {"Mara": (2000, 500), "Trina": (1000, 2500)})  # Mara owes Trina
one.session(day(2), {"Mara": (1000, 400), "Paolo": (1000, 1600)}, unit="chips")
live = make_session(one.host, table=one.table, state="open", game_date=day(4))
seats = games.add_participants(live.pk, one.host, [one.member(n).pk for n in ["Mara", "Miguel", "Carlo", "Trina", "Paolo", "Jerome", "Bea", "Anton"]], u())
for seat in seats:
    ledger.record_buy_in(live.pk, one.host, seat.pk, 100000, u())
games.transition(live.pk, one.host, "start", opening_buy_ins=False)
for n in range(3):
    make_session(one.host, table=make_table(one.host, name=f"Side table {n + 1}"), state="open", game_date=day(5 + n))

# 2. An open session that has not started. Mara is a player; "pia" hosts and belongs to this group only.
two = club("pia", "Sunday Garage Game")
join(two)
for name in ["Ana", "Ben", "Cho"]:
    two.member(name)
make_session(two.host, table=two.table, state="open", game_date=day(6))

# 3. Nothing played, a 60-character name. Mara is a host.
three = club("ivy", "The Extraordinarily Long Named Thursday Night Card Society X")
join(three, "host")

# 4. Nothing in progress; the last session was one Mara sat out, and she is owed from an earlier one.
four = club("noel", "Tuesday Regulars")
join(four)
four.session(day(0), {"Mara": (500, 1300), "Dino": (800, 0)})  # Dino owes Mara
four.session(day(3), {"Dino": (500, 900), "Ely": (900, 500)})

# 5. A small group with one even session.
five = club("oscar", "Office Game")
join(five)
five.session(day(2), {"Mara": (500, 500), "Gil": (500, 500)})

manifest = {"viewer": "mara", "single": "pia", "groups": {k: c.group.pk for k, c in
            {"play": one, "open": two, "long": three, "owed": four, "even": five}.items()}, "live": live.pk}
Path("/private/tmp/pn-home-manifest.json").write_text(json.dumps(manifest))
print("HOME", manifest)
