"""Fixture for share.mjs. Run only on a fresh temporary SQLite database; it needs no other seed.

Three closed sessions of host ``hana``: four players over two sets, twelve players with long
names and large amounts, and a chips game where nobody owes. Writes their ids to a manifest.
"""
import datetime, json, uuid
from django.contrib.auth import get_user_model
from django.utils import timezone
from games import services as games
from games.models import Participant
from groups import services as groups
from groups.models import Member
from ledger import services as ledger
from settlement import services as settlement
User = get_user_model()
hana = User.objects.create_user("hana", password="tablestakes-91")
host = groups.create_group(hana, "Kamuning Card Club")
ben = Member.objects.create(group=host.group, user=User.objects.create_user("ben", password="tablestakes-91"), display_name="Ben")
names = ["Miguel", "Carlo", "Maria Concepcion de los Santos", "Trina", "Paolo", "Jerome", "Bea", "Anton", "Bernadette Villanueva-Reyes", "Jo", "Mikaela"]
everyone = [ben.pk] + [groups.add_roster_player(host, n).pk for n in names]
u = uuid.uuid4
def play(s, ids, figures):
    people = {p.member_id: p for p in Participant.objects.filter(session=s)}
    for member_id, (buy_in, _) in zip(ids, figures):
        ledger.record_buy_in(s.pk, host, people[member_id].pk, buy_in, u())
    games.transition(s.pk, host, "end")
    for member_id, (_, cash_out) in zip(ids, figures):
        ledger.record_cash_out(s.pk, host, people[member_id].pk, cash_out, u())
    settlement.finalize(s.pk, host)
def session(name, days_ago, ids, sets, seats=9, unit="php", top=500000000):
    t = games.create_table(host, name, seats)
    scale = 1 if unit == "chips" else 100
    s = games.create_session(host, {"table_id": t.pk, "game_date": timezone.localdate() - datetime.timedelta(days=days_ago), "location": "Kamuning", "game_type": "nlh", "unit": unit,
        "small_blind": 10 * scale, "big_blind": 20 * scale, "min_buy_in": 500 * scale, "max_buy_in": top, "default_buy_in": 1000 * scale})
    games.transition(s.pk, host, "open")
    for member_id in ids:
        games.add_participant(s.pk, host, member_id)
    games.transition(s.pk, host, "start", opening_buy_ins=False)
    play(s, ids, [(a * scale, b * scale) for a, b in sets[0]])
    for figures in sets[1:]:
        nxt = games.start_next_set(s.night_id, host)
        games.transition(nxt.pk, host, "start", opening_buy_ins=False)
        play(nxt, ids, [(a * scale, b * scale) for a, b in figures])
    settlement.close_night(s.night_id, host)
    return s.night_id
small = session("Friday table", 0, everyone[:4], [[(1000, 1600), (1000, 700), (500, 200), (1500, 1500)], [(1000, 600), (1000, 1400), (500, 500), (1000, 1000)]])
big = session("Bonifacio Global City Saturday Deep Stack", 1, everyone, [[
    (250000, 809567), (100000, 0), (100000, 250000), (150000, 0), (100000, 100000), (50000, 75500), (100000, 0), (100000, 64933),
    (100000, 0), (50000, 0), (100000, 0), (100000, 0)]], seats=12)
even = session("Chips night", 2, everyone[:3], [[(1000, 1000), (1000, 1000), (500, 500)]], unit="chips")
json.dump({"small": small, "big": big, "even": even}, open("/private/tmp/pn-share-manifest.json", "w"))
