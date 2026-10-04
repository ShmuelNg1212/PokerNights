"""Run after seed.py, seed_end_set.py and seed_night.py on a fresh temporary DB. Archive and delete fixtures."""
import json
from pathlib import Path
from games import services as games
from games.models import GameNight, GameSession
from games.tests.helpers import make_session
from groups import services as groups
from groups.models import Member
from settlement.queries import unpaid_in
host = Member.objects.get(user__username='hana', role='host')
unpaid = next(n for n in GameNight.objects.filter(group=host.group, status='closed').order_by('pk') if unpaid_in(n))
empty = make_session(host, state='open', table_name='Mistaken session')
games.transition(empty.pk, host, 'cancel', 'made by mistake')
second = make_session(host, state='open', table_name='Second mistake')
games.transition(second.pk, host, 'cancel', 'made by mistake')
live = GameSession.objects.filter(group=host.group, state='running').first()
club = groups.create_group(host.user, 'Empty Club')
long = groups.create_group(host.user, 'TheVeryLongUnbrokenGroupNameThatMustWrapInsideItsContainer')
manifest = {'group': host.group_id, 'unpaid': unpaid.pk, 'unpaid_set': unpaid.sets.first().pk, 'empty': empty.night_id,
            'second': second.night_id, 'live': live.night_id, 'club': club.group_id, 'long': long.group_id}
Path('/private/tmp/pn-archive-manifest.json').write_text(json.dumps(manifest))
print(manifest)
