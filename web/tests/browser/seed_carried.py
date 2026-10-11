"""Fixture for carried transfers. Run alone on a fresh temporary SQLite database.

Host hana and players Ben (login), Ana, Carlo and Dee. Two closed sessions with unpaid transfers
(Ana owes Ben ₱500; Carlo owes Dee ₱300, and Ben owes Ana ₱120 in the second), and a third session
of all four, finalized and ready to close.
"""
import datetime, json, uuid
from django.contrib.auth import get_user_model
from django.utils import timezone
from games import services as games
from groups import services as groups
from groups.models import Member
from ledger import services as ledger
from settlement import services as settlement
User = get_user_model()
hana = User.objects.create_user("hana", password="tablestakes-91")
host = groups.create_group(hana, "Kamuning Card Club")
ben = Member.objects.create(group=host.group, user=User.objects.create_user("ben", password="tablestakes-91"), display_name="Ben")
people = {"Ben": ben, **{n: groups.add_roster_player(host, n) for n in ["Ana", "Carlo", "Dee"]}}
u = uuid.uuid4
def play(name, days_ago, nets, close=False):
    t = games.create_table(host, name, 9)
    s = games.create_session(host, {"table_id": t.pk, "game_date": timezone.localdate() - datetime.timedelta(days=days_ago), "location": "Kamuning", "game_type": "nlh",
        "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 500000, "default_buy_in": 100000})
    games.transition(s.pk, host, "open")
    seats = {n: games.add_participant(s.pk, host, people[n].pk) for n in nets}
    for n in nets: ledger.record_buy_in(s.pk, host, seats[n].pk, 100000, u())
    games.transition(s.pk, host, "start", opening_buy_ins=False)
    games.transition(s.pk, host, "end")
    for n, net in nets.items(): ledger.record_cash_out(s.pk, host, seats[n].pk, 100000 + net * 100, u())
    settlement.finalize(s.pk, host)
    if close: settlement.close_night(s.night_id, host)
    return s.night_id
first = play("Garage table", 7, {"Ana": -500, "Ben": 500}, close=True)
second = play("Rooftop table", 3, {"Carlo": -300, "Dee": 300, "Ben": -120, "Ana": 120}, close=True)
tonight = play("Kitchen table", 0, {"Ana": 250, "Ben": -400, "Carlo": 350, "Dee": -200})
manifest = {"first": first, "second": second, "tonight": tonight, "group": host.group_id}
open("/private/tmp/pn-carried-manifest.json", "w").write(json.dumps(manifest))
print("CARRIED_IDS", manifest)
