"""The worst realistic data for a group's Players, Settings and Stats tabs (break-ui, Slice D), on a fresh temporary database.

Names at the 60-character limit, names with no space to wrap at, one letter, diacritics, right-to-left, emoji;
a 60-character group, table and preset; a contact near 120; 16 players; wins and losses in
the millions of pesos; three active invite links.

    manage.py shell < web/tests/browser/seed_break_group.py
"""
import datetime
import uuid

from django.contrib.auth import get_user_model

from games import services as games
from games.tests.helpers import make_session, make_table
from groups import services as groups
from groups.models import Member
from ledger import services as ledger
from settlement import services as settlement

User = get_user_model()
LONG_GROUP = "Aleksandra Wiśniewska-Kowalczyk's Thursday Night Card Society"[:60]
host = groups.create_group(User.objects.create_user("aleksandra", password="tablestakes-91"), LONG_GROUP)
group = host.group
# A host whose own name is at the limit, and who has a login, so "(you)" and Host both show on the longest row.
groups.rename_self(host, "Aleksandra Wiśniewska-Kowalczyk de la Cruz y Fernández III")
login = Member.objects.create(group=group, user=User.objects.create_user("bartholomew", password="tablestakes-91"), display_name="bartholomew.fitzgerald@northwind-industries.example.com"[:60])
names = ["Jo", "J", "Đặng Thị Ngọc Hân", "王秀英", "نور الهدى عبد الرحمن", "🦊 Fox", "👩🏽‍💻 Priya", "Seán O'Brien-Ó Súilleabháin", "Christopher Alexander Montgomery III", "Konstantin Oberhauser-Wettstein", "María José de la Cruz y Fernández", "dana", "Ana", "Ben"]
members = groups.add_roster_players(host, names)
groups.edit_member(host, members[8].pk, members[8].display_name, "Ask at the Kamuning branch, ground floor, beside the pharmacy. Text first. Viber only after 9 p.m. 0917 555 0101.")
table = make_table(host, name="The long table in the back room of Tita Baby's house, Kamuning"[:60])
games.save_preset(host, {"name": "Saturday high stakes for the regulars, with the bigger blinds"[:60], "game_type": "nlh", "unit": "php", "small_blind": 100000, "big_blind": 200000, "min_buy_in": 10000000, "max_buy_in": 49999999, "default_buy_in": 20000000})


def play(when, unit_big, winners, losers):
    session = make_session(host, table=table, state="open", game_date=when, min_buy_in=unit_big, max_buy_in=unit_big, default_buy_in=unit_big)
    seats = games.add_participants(session.pk, host, [m.pk for m in winners + losers], uuid.uuid4())
    games.transition(session.pk, host, "start", opening_buy_ins=False)
    for seat in seats:
        ledger.record_buy_in(session.pk, host, seat.pk, unit_big, uuid.uuid4())
    games.transition(session.pk, host, "end")
    total = unit_big * len(seats)
    outs = [total] + [0] * (len(seats) - 1)
    for seat, cashed in zip(seats, outs):
        ledger.record_cash_out(session.pk, host, seat.pk, cashed, uuid.uuid4())
    settlement.finalize(session.pk, host)
    settlement.close_night(session.night_id, host)


# Winning everything in a night, three times over, so the board's figures are the widest they get.
for day in (1, 8, 15):
    play(datetime.date(2026, 10, day), 49999999, [members[8]], [host, login, members[0], members[1], members[2]])
for day in (2, 9):
    play(datetime.date(2026, 9, day), 100000, [members[9]], [members[3], members[4], members[5], members[6]])

for _ in range(3):
    groups.create_invite(host)
print("break seed: group", group.pk, "first", members[0].pk, "long", members[8].pk)
