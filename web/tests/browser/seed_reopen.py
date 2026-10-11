"""Fixture for reopen.mjs. Run only on a fresh temporary SQLite database; it needs no other seed.

Three sessions of host ``hana``: one open with a finalized set, one closed with two sets and
nothing paid, one closed with a transfer marked paid. Writes their ids to a manifest.
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
ids = [ben.pk] + [groups.add_roster_player(host, n).pk for n in ["Miguel", "Carlo", "Maria Concepcion de los Santos"]]
u = uuid.uuid4
def play(s, figures):
    people = {p.member_id: p for p in Participant.objects.filter(session=s)}
    for member_id, (buy_in, _) in zip(ids, figures):
        ledger.record_buy_in(s.pk, host, people[member_id].pk, buy_in * 100, u())
    games.transition(s.pk, host, "end")
    for member_id, (_, cash_out) in zip(ids, figures):
        ledger.record_cash_out(s.pk, host, people[member_id].pk, cash_out * 100, u())
    settlement.finalize(s.pk, host)
def session(name, days_ago, sets):
    t = games.create_table(host, name, 9)
    s = games.create_session(host, {"table_id": t.pk, "game_date": timezone.localdate() - datetime.timedelta(days=days_ago), "location": "Kamuning", "game_type": "nlh",
        "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 500000, "default_buy_in": 100000})
    games.transition(s.pk, host, "open")
    for member_id in ids:
        games.add_participant(s.pk, host, member_id)
    games.transition(s.pk, host, "start", opening_buy_ins=False)
    play(s, sets[0])
    made = [s.pk]
    for figures in sets[1:]:
        nxt = games.start_next_set(s.night_id, host)
        games.transition(nxt.pk, host, "start", opening_buy_ins=False)
        play(nxt, figures)
        made.append(nxt.pk)
    return s.night_id, made
first = [(1000, 1600), (1000, 700), (500, 200), (1500, 1500)]
second = [(1000, 600), (1000, 1400), (500, 500), (1000, 1000)]
open_night, open_sets = session("Friday table", 0, [first])
closed_night, closed_sets = session("Saturday table", 1, [first, second])
settlement.close_night(closed_night, host)
paid_night, paid_sets = session("Sunday table", 2, [first])
plan = settlement.close_night(paid_night, host)
settlement.mark_paid(paid_night, host, plan.transfers.first().pk, u())
json.dump({"open": {"night": open_night, "sets": open_sets}, "closed": {"night": closed_night, "sets": closed_sets},
           "paid": {"night": paid_night, "sets": paid_sets}}, open("/private/tmp/pn-reopen-manifest.json", "w"))
