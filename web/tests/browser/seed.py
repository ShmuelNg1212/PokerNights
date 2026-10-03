"""Synthetic browser fixture. Run only on a fresh temporary SQLite database.

These records exercise the real services; login names/passwords are test data.
"""
import datetime, uuid
from unittest import mock
from django.contrib.auth import get_user_model
from django.utils import timezone
from games import services as games
from groups import services as groups
from groups.models import Member
from ledger import services as ledger
from ledger.models import FinalCount
from settlement import services as settlement
from settlement.models import Transfer
User = get_user_model()
hana = User.objects.create_user("hana", password="tablestakes-91")
host = groups.create_group(hana, "Kamuning Card Club")
ben = Member.objects.create(group=host.group, user=User.objects.create_user("ben", password="tablestakes-91"), display_name="Ben")
names = ["Miguel", "Carlo", "Trina", "Paolo", "Jerome", "Bea", "Anton"]
ids = [groups.add_roster_player(host, n).pk for n in names]
u = uuid.uuid4
def game(table_name, loc, days_ago=0):
    t = games.create_table(host, table_name, 9)
    s = games.create_session(host, {"table_id": t.pk, "game_date": timezone.localdate() - datetime.timedelta(days=days_ago), "location": loc, "game_type": "nlh",
        "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 500000, "default_buy_in": 100000})
    games.transition(s.pk, host, "open")
    return s
ago = lambda h: mock.patch("games.services.timezone.now", return_value=timezone.now() - datetime.timedelta(hours=h))
# 1. finalized and settled
a = game("Garage table", "Carlo's garage", 7)
pa = games.add_participants(a.pk, host, ids[:5] + [ben.pk], u())
for p, amt in zip(pa, [100000, 200000, 100000, 300000, 100000, 150000]):
    ledger.record_buy_in(a.pk, host, p.pk, amt, u())
with ago(5): games.transition(a.pk, host, "start")
games.transition(a.pk, host, "end")
ledger.confirm_counts(a.pk, host, {p.pk: amt for p, amt in zip(pa, [345000, 0, 182500, 120000, 237500, 65000])}, u())
ledger.cash_out_counted(a.pk, host, list(FinalCount.objects.filter(participant__session=a, is_current=True).values_list("pk", flat=True)), u())
settlement.finalize(a.pk, host)
settlement.close_night(a.night_id, host)
tr = Transfer.objects.filter(plan__night_id=a.night_id).first()
settlement.mark_paid(a.night_id, host, tr.pk, u())
# 2. counting up
b = game("Rooftop table", "Trina's rooftop", 1)
pb = games.add_participants(b.pk, host, ids[:6], u())
for p, amt in zip(pb, [100000, 100000, 250000, 100000, 200000, 100000]):
    ledger.record_buy_in(b.pk, host, p.pk, amt, u())
with ago(4): games.transition(b.pk, host, "start")
games.transition(b.pk, host, "end")
ledger.confirm_counts(b.pk, host, {pb[0].pk: 310000, pb[1].pk: 45000, pb[2].pk: 0}, u())
c0 = FinalCount.objects.filter(participant=pb[0], is_current=True).first()
ledger.cash_out_counted(b.pk, host, [c0.pk], u())
# 3. live
c = game("Friday table", "Miguel's place")
pc = games.add_participants(c.pk, host, ids + [ben.pk], u())
for p, amt in zip(pc, [100000, 100000, 200000, 100000, 100000, 150000, 100000, 100000]):
    ledger.record_buy_in(c.pk, host, p.pk, amt, u())
with ago(2): games.transition(c.pk, host, "start")
ledger.record_buy_in(c.pk, host, pc[1].pk, 100000, u())
ledger.record_buy_in(c.pk, host, pc[4].pk, 200000, u())
ledger.record_cash_out(c.pk, host, pc[6].pk, 265000, u(), left=True)
# 4. setup, empty
d = games.create_session(host, {"table_id": games.create_table(host, "Sunday table", 6).pk, "game_date": timezone.localdate() + datetime.timedelta(days=2), "location": "", "game_type": "nlh",
    "small_blind": 500, "big_blind": 1000, "min_buy_in": 20000, "max_buy_in": 200000, "default_buy_in": 50000})
print("IDS", host.group.pk, a.pk, a.night_id, b.pk, c.pk, c.night_id, d.pk)

from games.tests.helpers import make_session, CHIP_STAKES
chips = make_session(host, state="open", table_name="Chip table", unit="chips", **CHIP_STAKES)
players = games.add_participants(chips.pk, host, ids + [ben.pk], u())
for player in players:
    ledger.record_buy_in(chips.pk, host, player.pk, 1000, u())
games.transition(chips.pk, host, "start")
