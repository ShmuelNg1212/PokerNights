"""Synthetic fixture for past_filters.mjs. Run only on a fresh temporary SQLite database.

Ben (player) has a settled night, a night with money still to pay, and a night he missed.
Hana (host) has a set counting up that started four hours ago and ended now.
"""
import datetime, json, uuid
from unittest import mock
from django.contrib.auth import get_user_model
from django.utils import timezone
from games import services as games
from groups import services as groups
from groups.models import Member
from ledger import services as ledger
from settlement import services as settlement
from settlement.models import Transfer
User = get_user_model()
u = uuid.uuid4
hana = User.objects.create_user("hana", password="tablestakes-91")
host = groups.create_group(hana, "Filter Club")
ben = Member.objects.create(group=host.group, user=User.objects.create_user("ben", password="tablestakes-91"), display_name="Ben")
carlo, dina = (groups.add_roster_player(host, n) for n in ("Carlo", "Dina"))
table = games.create_table(host, "Garage table", 9)
ago = lambda h: mock.patch("games.services.timezone.now", return_value=timezone.now() - datetime.timedelta(hours=h))
def game(days_ago):
    s = games.create_session(host, {"table_id": table.pk, "game_date": timezone.localdate() - datetime.timedelta(days=days_ago), "location": "Carlo's garage", "game_type": "nlh",
        "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 500000, "default_buy_in": 100000})
    games.transition(s.pk, host, "open")
    return s
def closed(days_ago, nets, paid=False):
    s = game(days_ago)
    seats = games.add_participants(s.pk, host, [m.pk for m in nets], u())
    for seat in seats:
        ledger.record_buy_in(s.pk, host, seat.pk, 100000, u())
    games.transition(s.pk, host, "start"); games.transition(s.pk, host, "end")
    for seat, net in zip(seats, nets.values()):
        ledger.record_cash_out(s.pk, host, seat.pk, 100000 + net, u())
    settlement.finalize(s.pk, host); settlement.close_night(s.night_id, host)
    if paid:
        for t in Transfer.objects.filter(plan__night_id=s.night_id):
            settlement.mark_paid(s.night_id, host, t.pk, u())
    return s.night_id
settled = closed(9, {ben: 20000, carlo: -20000}, paid=True)
owing = closed(5, {ben: -30000, dina: 30000})
away = closed(2, {carlo: 10000, dina: -10000})
counting = game(0)
seats = games.add_participants(counting.pk, host, [ben.pk, carlo.pk], u())
for seat in seats:
    ledger.record_buy_in(counting.pk, host, seat.pk, 100000, u())
with ago(4): games.transition(counting.pk, host, "start")
games.transition(counting.pk, host, "end")
json.dump({"group": host.group_id, "settled": settled, "owing": owing, "away": away, "counting": counting.pk},
          open("/private/tmp/pn-past-filters-manifest.json", "w"))
print("seeded")
