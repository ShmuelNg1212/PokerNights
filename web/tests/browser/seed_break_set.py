"""The worst realistic names for the set flow (break-ui), on a fresh temporary database.

Names at the 60-character limit, a name with no space to wrap at, an email as a name, one letter,
diacritics, right-to-left, emoji. Four sets of one table: a draft to set up and add players to,
an open set with its seats drawn, a set in play with buy-ins, a cash-out and a leaver, and a set
being counted. Host `aleksandra` has the longest name, so "(you)" and the host mark show on it.

    manage.py shell < web/tests/browser/seed_break_set.py
"""
import json
import uuid

from django.contrib.auth import get_user_model

from games import services as games
from games.tests.helpers import make_session, make_table
from groups import services as groups
from groups.models import Member
from ledger import services as ledger

User = get_user_model()
u = uuid.uuid4
host = groups.create_group(User.objects.create_user("aleksandra", password="tablestakes-91"), "Thursday Night Card Society")
groups.rename_self(host, "Aleksandra Wiśniewska-Kowalczyk de la Cruz y Fernández III")
email = Member.objects.create(group=host.group, user=User.objects.create_user("bartholomew", password="tablestakes-91"),
                              display_name="bartholomew.fitzgerald@northwind-industries.example.com")
names = ["J", "AlexandriaDeLaCruzWithAVeryLongUnbrokenDisplayName", "Christopher Alexander Montgomery III",
         "Seán O'Brien-Ó Súilleabháin", "نور الهدى عبد الرحمن", "👩🏽‍💻 Priya", "Đặng Thị Ngọc Hân", "Ben",
         "Konstantin Oberhauser-Wettstein", "María José de la Cruz y Fernández"]
roster = groups.add_roster_players(host, names)
nine = [host, email] + roster[:7]
table = make_table(host, name="The long table in the back room", seat_count=12)


def new_set(state, members):
    session = make_session(host, table=table, state=state)
    return session, games.add_participants(session.pk, host, [m.pk for m in members], u())


draft, _ = new_set("setup", nine[:6])
drawn, _ = new_set("open", nine)
games.draw_seats(drawn.pk, host, u())
games.choose_seat(drawn.pk, host, 0, u())
playing, seats = new_set("open", nine)
games.transition(playing.pk, host, "start", opening_buy_ins=False)
for seat in seats[:7]:
    ledger.record_buy_in(playing.pk, host, seat.pk, 100000, u())
ledger.record_buy_in(playing.pk, host, seats[1].pk, 100000, u())
ledger.record_cash_out(playing.pk, host, seats[2].pk, 250000, u())
games.set_left(playing.pk, host, seats[2].pk)
counting, cseats = new_set("open", nine)
games.transition(counting.pk, host, "start", opening_buy_ins=False)
for seat in cseats:
    ledger.record_buy_in(counting.pk, host, seat.pk, 100000, u())
games.transition(counting.pk, host, "end")
manifest = {"group": host.group_id, "draft": draft.pk, "drawn": drawn.pk, "playing": playing.pk, "counting": counting.pk,
            "count_player": cseats[0].pk}
open("/private/tmp/pn-break-set-manifest.json", "w").write(json.dumps(manifest))
print("BREAK_SET", manifest)
