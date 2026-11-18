"""Fixture for sheet drag and haptics. Run alone on a fresh temporary SQLite database.

Host hana (with player ben, who has a login) has one set in play with four players, for the buy-in and
cash-out sheets and their number keys; one set counting up whose books balance, for the haptic at that
moment; and one closed session of twelve players, for the long recap sheet.
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

play = make_session(host, state="open", table_name="Garage table", seat_count=6)
for p in games.add_participants(play.pk, host, [m.pk for m in [ben] + roster[:3]], u()):
    ledger.record_buy_in(play.pk, host, p.pk, 100000, u())
games.transition(play.pk, host, "start")

count = make_session(host, state="open", table_name="Porch table", seat_count=4)
pair = games.add_participants(count.pk, host, [ben.pk, roster[0].pk], u())
for p in pair: ledger.record_buy_in(count.pk, host, p.pk, 100000, u())
games.transition(count.pk, host, "start")
games.transition(count.pk, host, "end")
for p, cash in zip(pair, [150000, 50000]): ledger.record_cash_out(count.pk, host, p.pk, cash, u())

nets = [20000, 60000, 40000, 100000, 10000, 0, -10000, -20000, -30000, -40000, -50000, -80000]
done = make_session(host, state="open", table_name="Long table", seat_count=12)
people = games.add_participants(done.pk, host, [m.pk for m in [ben] + roster], u())
for p in people: ledger.record_buy_in(done.pk, host, p.pk, 100000, u())
games.transition(done.pk, host, "start")
games.transition(done.pk, host, "end")
for p, net in zip(people, nets): ledger.record_cash_out(done.pk, host, p.pk, 100000 + net, u())
settlement.finalize(done.pk, host)
settlement.close_night(done.night_id, host)

manifest = {"play": play.pk, "count": count.pk, "twelve": done.night_id}
open("/private/tmp/pn-drag-manifest.json", "w").write(json.dumps(manifest))
print("DRAG_IDS", manifest)
