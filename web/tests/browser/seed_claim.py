"""A group for claim.mjs, on a fresh temporary database: host ``rosa``; roster players without a login
(Tito Boy with a closed session, Lola, Nonoy, Pedro); ``benny`` in the group with nothing recorded;
``dana`` in the group with a session played; ``eli`` with an account and no group.

    manage.py shell < web/tests/browser/seed_claim.py
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
PASSWORD = "tablestakes-91"
host = groups.create_group(User.objects.create_user("rosa", password=PASSWORD), "Thursday Regulars")
group = host.group
tito, lola, nonoy, pedro = groups.add_roster_players(host, ["Tito Boy", "Lola", "Nonoy", "Pedro"])
benny = Member.objects.create(group=group, user=User.objects.create_user("benny", password=PASSWORD), display_name="benny")
dana = Member.objects.create(group=group, user=User.objects.create_user("dana", password=PASSWORD), display_name="dana")
User.objects.create_user("eli", password=PASSWORD)
table = make_table(host, name="Main table")

closed = make_session(host, table=table, state="open", game_date=datetime.date(2026, 10, 1))
seats = games.add_participants(closed.pk, host, [tito.pk, dana.pk], uuid.uuid4())
games.transition(closed.pk, host, "start", opening_buy_ins=False)
for seat in seats:
    ledger.record_buy_in(closed.pk, host, seat.pk, 100000, uuid.uuid4())
games.transition(closed.pk, host, "end")
for seat, cashed in zip(seats, (150000, 50000)):
    ledger.record_cash_out(closed.pk, host, seat.pk, cashed, uuid.uuid4())
settlement.finalize(closed.pk, host)
settlement.close_night(closed.night_id, host)
print("claim seed: group", group.pk)
