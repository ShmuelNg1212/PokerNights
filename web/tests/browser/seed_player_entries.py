"""Run after seed.py on a fresh temporary DB. One running set for player_entries.mjs: Ben and maria have logins, Anton has none."""
import json
import uuid
from pathlib import Path
from accounts.models import User
from games import services as games
from games.tests.helpers import make_session
from groups.models import Member
from ledger import services as ledger
host = Member.objects.get(user__username='hana', role='host')
ben = Member.objects.get(group=host.group, user__username='ben')
maria = Member.objects.create(group=host.group, user=User.objects.create_user('maria', password='tablestakes-91'), display_name='maria')
anton = Member.objects.filter(group=host.group, user__isnull=True).order_by('pk').first()
session = make_session(host, state='open', table_name='Entries table')
players = games.add_participants(session.pk, host, [maria.pk, ben.pk, anton.pk], uuid.uuid4())
for p in players: ledger.record_buy_in(session.pk, host, p.pk, 100000, uuid.uuid4())
games.transition(session.pk, host, 'start', opening_buy_ins=False)
manifest = {'set': session.pk, 'maria': players[0].pk, 'ben': players[1].pk, 'anton': players[2].pk}
Path('/private/tmp/pn-entries-manifest.json').write_text(json.dumps(manifest))
print('ENTRIES', manifest)
