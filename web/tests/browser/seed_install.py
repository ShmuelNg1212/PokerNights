"""Fixture for install_prompt.mjs. Run only on a fresh temporary SQLite database; it needs no other seed.

Host ``hana`` with one group and a live invite; ``ben`` a member; a closed session whose recap opens by itself.
"""
import json, uuid
from django.contrib.auth import get_user_model
from django.utils import timezone
from games import services as games
from games.models import Participant
from groups import services as groups
from groups.models import Invite, Member
from ledger import services as ledger
from settlement import services as settlement
User = get_user_model()
hana = User.objects.create_user("hana", password="tablestakes-91")
host = groups.create_group(hana, "Kamuning Card Club")
ben = Member.objects.create(group=host.group, user=User.objects.create_user("ben", password="tablestakes-91"), display_name="Ben")
User.objects.create_user("cara", password="tablestakes-91")
t = games.create_table(host, "Friday table", 9)
s = games.create_session(host, {"table_id": t.pk, "game_date": timezone.localdate(), "location": "Kamuning", "game_type": "nlh",
    "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 500000, "default_buy_in": 100000})
games.transition(s.pk, host, "open")
other = groups.add_roster_player(host, "Miguel")
for member_id in (ben.pk, other.pk):
    games.add_participant(s.pk, host, member_id)
games.transition(s.pk, host, "start", opening_buy_ins=False)
people = {p.member_id: p for p in Participant.objects.filter(session=s)}
for member_id in (ben.pk, other.pk):
    ledger.record_buy_in(s.pk, host, people[member_id].pk, 100000, uuid.uuid4())
games.transition(s.pk, host, "end")
ledger.record_cash_out(s.pk, host, people[ben.pk].pk, 150000, uuid.uuid4())
ledger.record_cash_out(s.pk, host, people[other.pk].pk, 50000, uuid.uuid4())
settlement.finalize(s.pk, host)
settlement.close_night(s.night_id, host)
made = groups.create_invite(host)
token = made[1] if isinstance(made, tuple) else getattr(made, "token", None)
json.dump({"night": s.night_id, "group": host.group_id, "invite": token}, open("/private/tmp/pn-install-manifest.json", "w"))
