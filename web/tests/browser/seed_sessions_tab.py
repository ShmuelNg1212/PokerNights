"""The Sessions tab's synthetic group. Run alone on a fresh temporary database, then serve it on 127.0.0.1:8765.

Host ``hana`` and player ``ben`` (password ``tablestakes-91``) in "Friday Game". Ben sits at set 2 in play at
the Garage and at an open set Upstairs; another set is in play Upstairs without him; a draft for next week is
for hosts. Past: five pesos sessions this year with debts both ways, one with ₱1,999,999.98 and a 60-character
table name, a chips session, two sessions last year, and one archived. Writes the ids to the manifest.
"""
import datetime
import json
import uuid

from django.contrib.auth import get_user_model
from django.utils import timezone

from games import services as games
from games.tests.helpers import CHIP_STAKES, make_session, make_table
from groups import services as groups
from ledger import services as ledger
from settlement import services as settlement

u = uuid.uuid4
User = get_user_model()
host = groups.create_group(User.objects.create_user('hana', password='tablestakes-91'), 'Friday Game')
ben = groups.add_roster_player(host, 'Ben')
ben.user = User.objects.create_user('ben', password='tablestakes-91')
ben.save()
people = [host, ben, *(groups.add_roster_player(host, n) for n in ['Carlo', 'Dina', 'Ely', 'Fritz', 'Gino', 'Hector'])]
garage = make_table(host, name='Garage', seat_count=9)
upstairs = make_table(host, name='Upstairs', seat_count=9)
long = make_table(host, name="The back room behind Tito Boy's sari-sari store, Marikina", seat_count=9)
today = timezone.localdate()


def played(table, day, nets, *, unit='php', close=True):
    """A session whose players (from the start of ``people``) end with these nets, in centavos or chips."""
    stakes = {**CHIP_STAKES, 'unit': 'chips'} if unit == 'chips' else {}
    bought = max(1000 if unit == 'chips' else 100000, *(-n for n in nets))
    if bought > 200000:
        stakes['max_buy_in'] = bought
    s = make_session(host, table=table, state='open', game_date=day, **stakes)
    seats = games.add_participants(s.pk, host, [m.pk for m in people[:len(nets)]], u())
    for seat in seats:
        ledger.record_buy_in(s.pk, host, seat.pk, bought, u())
    games.transition(s.pk, host, 'start')
    games.transition(s.pk, host, 'end')
    for seat, net in zip(seats, nets):
        ledger.record_cash_out(s.pk, host, seat.pk, bought + net, u())
    settlement.finalize(s.pk, host)
    if close:
        settlement.close_night(s.night_id, host)
    return s


week = datetime.timedelta(days=7)
played(upstairs, today - week, [50000, -20000, -30000, 0])            # Ben pays
played(garage, today - 2 * week, [-10000, 40000, -30000])              # Ben is paid
played(long, today - 3 * week, [199999998, -199999998])                # Ben did not play
played(garage, today - 5 * week, [0, 15000, -15000])
played(upstairs, today - 6 * week, [-600, 600], unit='chips')
played(garage, datetime.date(today.year - 1, 11, 6), [20000, -20000])
played(garage, datetime.date(today.year - 1, 12, 4), [-5000, 5000])
archived = played(upstairs, today - 8 * week, [10000, -10000])
games.archive_night(archived.night_id, host)

first = played(garage, today, [30000, -30000, 0, 0, 0, 0, 0, 0], close=False)
second = games.start_next_set(first.night_id, host)
games.transition(second.pk, host, 'start')
other = make_session(host, table=upstairs, state='running', game_date=today)
games.add_participants(other.pk, host, [people[0].pk, *(m.pk for m in people[2:5])], u())
waiting = make_session(host, table=upstairs, state='open', game_date=today)
games.add_participant(waiting.pk, host, ben.pk)
draft = make_session(host, table=garage, state='setup', game_date=today + week)

manifest = {'group': host.group_id, 'mine_live': second.pk, 'other_live': other.pk, 'mine_open': waiting.pk, 'draft': draft.pk}
with open('/private/tmp/pn-sessions-tab-manifest.json', 'w') as f:
    json.dump(manifest, f)
print(manifest)
