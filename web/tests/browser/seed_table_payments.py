"""Fixture for payments at the table. Run alone on a fresh temporary SQLite database.

Host hana and players Ben (login), Ana and a long-named player. Tonight's set is running: Ben won
₱4,250.50 and left early; one table payment is already recorded and one undone. A second session
is closed with a table payment of ₱1,234,567 subtracted.
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
long_name = "Maria Concepcion Dela Cruz-Villanueva"
people = {"Ben": ben, **{n: groups.add_roster_player(host, n) for n in ["Ana", long_name]}}
u = uuid.uuid4
def session(name, days_ago, buy=100000):
    t = games.create_table(host, name, 9)
    s = games.create_session(host, {"table_id": t.pk, "game_date": timezone.localdate() - datetime.timedelta(days=days_ago), "location": "Kamuning", "game_type": "nlh",
        "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 500000000, "default_buy_in": buy})
    games.transition(s.pk, host, "open")
    seats = {n: games.add_participant(s.pk, host, people[n].pk) for n in people}
    for n in people: ledger.record_buy_in(s.pk, host, seats[n].pk, buy, u())
    games.transition(s.pk, host, "start", opening_buy_ins=False)
    return s, seats
tonight, seats = session("Kitchen table", 0)
ledger.record_cash_out(tonight.pk, host, seats["Ben"].pk, 100000 + 425050, u(), left=True)
settlement.record_table_payment(tonight.night_id, host, people[long_name].pk, people["Ana"].pk, 15000, u())
mistake = settlement.record_table_payment(tonight.night_id, host, people["Ana"].pk, people["Ben"].pk, 20000, u())
settlement.reverse_table_payment(tonight.night_id, host, mistake.pk, "Wrong player")
closed, cseats = session("Rooftop table", 2, buy=300000000)
settlement.record_table_payment(closed.night_id, host, people[long_name].pk, people["Ben"].pk, 123456700, u())
games.transition(closed.pk, host, "end")
for n, out in {"Ben": 450000000, "Ana": 200000000, long_name: 250000000}.items():
    ledger.record_cash_out(closed.pk, host, cseats[n].pk, out, u())
settlement.finalize(closed.pk, host)
settlement.close_night(closed.night_id, host)
manifest = {"tonight": tonight.night_id, "set": tonight.pk, "closed": closed.night_id, "ben": ben.pk, "ben_participant": seats["Ben"].pk}
open("/private/tmp/pn-table-pay-manifest.json", "w").write(json.dumps(manifest))
print("TABLE_PAY_IDS", manifest)
