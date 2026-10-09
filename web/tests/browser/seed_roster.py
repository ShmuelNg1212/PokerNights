"""A group for roster.mjs, on a fresh temporary database: host ``rosa``, a player with a login,
players without one, a closed session with an unpaid transfer, a running set and a removed player.

    manage.py shell < web/tests/browser/seed_roster.py
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
host = groups.create_group(User.objects.create_user("rosa", password="tablestakes-91"), "Thursday Regulars")
group = host.group
dani = Member.objects.create(group=group, user=User.objects.create_user("dani", password="tablestakes-91"), display_name="dani")
ana, ben, carlo, gone = groups.add_roster_players(host, ["Ana", "Ben", "Carlo Maria Dela Cruz-Santos", "Tito Boy"])
table = make_table(host, name="Main table")

closed = make_session(host, table=table, state="open", game_date=datetime.date(2026, 10, 1))
seats = games.add_participants(closed.pk, host, [ana.pk, ben.pk, gone.pk], uuid.uuid4())
games.transition(closed.pk, host, "start", opening_buy_ins=False)
for seat, cashed in zip(seats, (150000, 50000, 100000)):
    ledger.record_buy_in(closed.pk, host, seat.pk, 100000, uuid.uuid4())
games.transition(closed.pk, host, "end")
for seat, cashed in zip(seats, (150000, 50000, 100000)):
    ledger.record_cash_out(closed.pk, host, seat.pk, cashed, uuid.uuid4())
settlement.finalize(closed.pk, host)
settlement.close_night(closed.night_id, host)

running = make_session(host, table=table, state="open", game_date=datetime.date(2026, 10, 9))
games.add_participants(running.pk, host, [carlo.pk], uuid.uuid4())
games.transition(running.pk, host, "start", opening_buy_ins=False)

groups.remove_member(host, gone.pk)
print("roster seed: group", group.pk, "ben", ben.pk, "carlo", carlo.pk, "dani", dani.pk)
