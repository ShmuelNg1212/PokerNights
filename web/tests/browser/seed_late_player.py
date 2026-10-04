"""Synthetic late-join fixtures; run after seed.py on a temporary database."""
import json, uuid
from pathlib import Path
from groups.models import Member
from games import services as games
from games.tests.helpers import make_session, CHIP_STAKES
host=Member.objects.get(user__username='hana',role='host')
roster=list(Member.objects.filter(group=host.group,status='active'))
ids={}
for name,unit,seats,all_seated in [('running','php',12,True),('full','php',2,False),('stale','php',3,False),('chips','chips',3,False)]:
 s=make_session(host,state='open',table_name='Late '+name,seat_count=seats,unit=unit,**(CHIP_STAKES if unit=='chips' else {}))
 games.add_participants(s.pk,host,[m.pk for m in (roster if all_seated else roster[:2])],uuid.uuid4())
 games.transition(s.pk,host,'start')
 ids[name]=s.pk
Path('/private/tmp/pn-late-manifest.json').write_text(json.dumps(ids));print(ids)
