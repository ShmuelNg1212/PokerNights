"""Fresh temporary database only. Two hosts (hana, ivy), a player with a login (ben) and two roster
players, at one set that is counting up. Login names and passwords are test data."""
import json, uuid
from pathlib import Path
from django.contrib.auth import get_user_model
from groups import services as groups
from groups.models import Member
from games.tests.helpers import make_session
from games import services as games
from ledger import services as ledger

User = get_user_model()
hana = User.objects.create_user("hana", password="tablestakes-91")
host = groups.create_group(hana, "Two-host table")
ivy = Member.objects.create(group=host.group, user=User.objects.create_user("ivy", password="tablestakes-91"),
                            display_name="Ivy", role=Member.Role.HOST)
ben = Member.objects.create(group=host.group, user=User.objects.create_user("ben", password="tablestakes-91"), display_name="Ben")
cara = groups.add_roster_player(host, "Cara")
dino = groups.add_roster_player(host, "Dino")
s = make_session(host, state="open", table_name="Two-host check")
ps = games.add_participants(s.pk, host, [ben.pk, cara.pk, dino.pk, ivy.pk], uuid.uuid4())
for p in ps:
    ledger.record_buy_in(s.pk, host, p.pk, 100000, uuid.uuid4())
games.transition(s.pk, host, "start")
games.transition(s.pk, host, "end")
manifest = {"set": s.pk, "night": s.night_id, "p": {p.member.display_name: p.pk for p in ps}}
Path("/private/tmp/pn-multi-host-manifest.json").write_text(json.dumps(manifest))
print(manifest)
