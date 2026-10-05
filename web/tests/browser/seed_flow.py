"""Run after seed.py on a fresh temporary DB. Sets for flow.mjs (motion on the live set page)."""
import json
import uuid
from pathlib import Path
from games import services as games
from games.tests.helpers import make_session
from groups.models import Member
from ledger import services as ledger
host = Member.objects.get(user__username='hana', role='host')
roster = list(Member.objects.filter(group=host.group, user__isnull=True).order_by('pk'))
manifest = {}
def table(key, state, count, money=True):
    session = make_session(host, state='open', table_name='Flow ' + key)
    players = games.add_participants(session.pk, host, [m.pk for m in roster[:count]], uuid.uuid4())
    if money:
        for p in players: ledger.record_buy_in(session.pk, host, p.pk, 100000, uuid.uuid4())
    if state == 'running': games.transition(session.pk, host, 'start', opening_buy_ins=False)
    manifest[key] = {'set': session.pk, 'players': [p.pk for p in players], 'spare': [m.pk for m in roster[count:]]}
for key in ('rows', 'wide', 'still', 'plain'): table(key, 'running', 4)
table('count', 'running', 2)
table('join', 'open', 3, money=False)
Path('/private/tmp/pn-flow-manifest.json').write_text(json.dumps(manifest))
print('FLOW', manifest)
