"""The profile's synthetic history. Run after seed.py and seed_night.py on a fresh temporary DB.

Gives ``ben`` closed sessions in two more groups: a pesos group where he wins over five
nights, and a chips group with a long name. Hana's group already holds his pesos and chips.
"""
import datetime
import uuid

from django.contrib.auth import get_user_model

from games import services as games
from games.tests.helpers import CHIP_STAKES, make_session
from groups import services as groups
from groups.models import Member
from ledger import services as ledger
from settlement import services as settlement

u = uuid.uuid4
ben = get_user_model().objects.get(username='ben')


def club(host_name, group_name):
    host = groups.create_group(get_user_model().objects.create_user(host_name, password='tablestakes-91'), group_name)
    me = Member.objects.create(group=host.group, user=ben, display_name='Ben')
    other = groups.add_roster_player(host, 'Carlo')
    return host, [me, other]


def night(host, members, day, nets, *, unit='php'):
    stakes = CHIP_STAKES if unit == 'chips' else {}
    s = make_session(host, state='open', table_name=f'Table {day:%b %d}', unit=unit, game_date=day, **stakes)
    seats = games.add_participants(s.pk, host, [m.pk for m in members], u())
    bought = 1000 if unit == 'chips' else 100000
    for seat in seats:
        ledger.record_buy_in(s.pk, host, seat.pk, bought, u())
    games.transition(s.pk, host, 'start')
    games.transition(s.pk, host, 'end')
    for seat, net in zip(seats, nets):
        ledger.record_cash_out(s.pk, host, seat.pk, bought + net, u())
    settlement.finalize(s.pk, host)
    settlement.close_night(s.night_id, host)


host, members = club('sunny', 'Sunday Game')
for weeks, net in enumerate([45000, -12000, 30000, 80000, -25000]):
    night(host, members, datetime.date(2026, 8, 2) + datetime.timedelta(weeks=weeks), [net, -net])
host, members = club('chipper', 'The Thursday Night Chips League at Carlo’s Place, Quezon')
for weeks, net in enumerate([150, -40]):
    night(host, members, datetime.date(2026, 9, 3) + datetime.timedelta(weeks=weeks), [net, -net], unit='chips')
print('profile seeded')
