"""Fixture for RSVP. Run alone on a fresh temporary SQLite database.

Host hana and players ben, ana, carlo, dina (logins) and a long-named roster player without one.
"Friday table" is announced for 8:00 PM with 3 seats: carlo, ana and the long name are in, dina waits,
ben has not answered. "Back room" is a draft that is not announced yet.
"""
import datetime, json, uuid
from django.contrib.auth import get_user_model
from django.utils import timezone
from games import rsvp, services as games
from groups import services as groups
from groups.models import Member
User = get_user_model()
hana = User.objects.create_user("hana", password="tablestakes-91")
host = groups.create_group(hana, "Kamuning Card Club")
people = {n: Member.objects.create(group=host.group, user=User.objects.create_user(n, password="tablestakes-91"), display_name=n.title())
          for n in ["ben", "ana", "carlo", "dina"]}
long_one = groups.add_roster_player(host, "Maria Concepcion Dela Cruz-Villanueva y Santos de los Reyes")
stakes = {"small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 200000, "default_buy_in": 100000}
def draft(name, days):
    t = games.create_table(host, name, 9)
    return games.create_session(host, {"table_id": t.pk, "game_date": timezone.localdate() + datetime.timedelta(days=days),
                                       "location": "Kamuning", "game_type": "nlh", **stakes})
friday = draft("Friday table", 3)
back = draft("Back room", 5)
rsvp.announce(friday.night_id, host, start_time=datetime.time(20, 0), seat_limit=3)
for m in (people["carlo"], people["ana"]):
    rsvp.answer(friday.night_id, m, m.pk, True, uuid.uuid4())
rsvp.answer(friday.night_id, host, long_one.pk, True, uuid.uuid4())
rsvp.answer(friday.night_id, people["dina"], people["dina"].pk, True, uuid.uuid4())
json.dump({"group": host.group_id, "friday": friday.night_id, "friday_set": friday.pk, "back": back.night_id,
           "ben": people["ben"].pk, "dina": people["dina"].pk}, open("/private/tmp/pn-rsvp-manifest.json", "w"))
print("seeded")
