"""A group for stats.mjs, on a fresh temporary database: host ``rosa`` and player ``dani`` with logins,
seven roster players, fourteen pesos sessions from June to October 2026 and four chips sessions. One player
came once, one was removed, and the first four sessions have no recorded time. Figures are synthetic.

    manage.py shell < web/tests/browser/seed_stats.py
"""
import datetime
import random
import uuid

from django.contrib.auth import get_user_model

from games import services as games
from games.tests.helpers import CHIP_STAKES, make_session, make_table
from groups import services as groups
from groups.models import Member
from ledger import services as ledger
from ledger.models import PlayerResult
from settlement import services as settlement

User = get_user_model()
rng = random.Random(7)
host = groups.create_group(User.objects.create_user("rosa", password="tablestakes-91"), "Thursday Regulars")
group = host.group
dani = Member.objects.create(group=group, user=User.objects.create_user("dani", password="tablestakes-91"), display_name="dani")
names = ["Ana", "Ben", "Carlo Maria Dela Cruz-Santos", "Eli", "Fe", "Gio", "Tito Boy", "Newcomer"]
roster = dict(zip(names, groups.add_roster_players(host, names)))
regulars = [host, dani] + [roster[n] for n in names[:7]]
table = make_table(host, name="Main table")
# How each regular tends to do, so the board has a shape.
lean = {host.pk: 1.25, dani.pk: 0.9, roster["Ana"].pk: 1.5, roster["Ben"].pk: 0.55, roster["Eli"].pk: 1.0,
        roster["Fe"].pk: 1.1, roster["Gio"].pk: 0.7, roster["Tito Boy"].pk: 0.8, roster["Carlo Maria Dela Cruz-Santos"].pk: 1.05}


def play(day, players, step, **settings):
    one = make_session(host, table=table, state="open", game_date=day, **settings)
    seats = games.add_participants(one.pk, host, [m.pk for m in players], uuid.uuid4())
    games.transition(one.pk, host, "start", opening_buy_ins=False)
    bought = []
    for seat in seats:
        buys = 1 + (rng.random() < 0.35) + (rng.random() < 0.1)
        for _ in range(buys):
            ledger.record_buy_in(one.pk, host, seat.pk, 1000 * step, uuid.uuid4())
        bought.append(buys * 1000 * step)
    weights = [rng.uniform(0.1, 1.9) * lean.get(m.pk, 1) for m in players]
    total, units = sum(bought), sum(bought) // (100 * step)
    shares = [int(units * w / sum(weights)) for w in weights]
    shares[0] += units - sum(shares)
    games.transition(one.pk, host, "end")
    for seat, share in zip(seats, shares):
        ledger.record_cash_out(one.pk, host, seat.pk, share * 100 * step, uuid.uuid4())
    settlement.finalize(one.pk, host)
    settlement.close_night(one.night_id, host)
    return one


days = [datetime.date(2026, 6, 4) + datetime.timedelta(days=9 * n) for n in range(14)]
for index, day in enumerate(days):
    players = [host] + rng.sample(regulars[1:], rng.randint(4, 6))
    if index == 12:
        players.append(roster["Newcomer"])
    one = play(day, players, 100)
    results = PlayerResult.objects.filter(finalization__session=one)
    if index < 4:
        results.update(play_seconds=None)
    else:
        for result in results:
            PlayerResult.objects.filter(pk=result.pk).update(play_seconds=rng.randint(2 * 3600, 5 * 3600))
for day in days[2:10:2]:
    play(day, [host, dani, roster["Ana"], roster["Ben"]], 1, **CHIP_STAKES, unit="chips")
groups.remove_member(host, roster["Tito Boy"].pk)
print("stats seed: group", group.pk, "rosa", host.pk, "ana", roster["Ana"].pk, "newcomer", roster["Newcomer"].pk)
