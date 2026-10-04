"""Run after seed.py, seed_end_set.py and seed_night.py on a fresh temporary DB."""
import json
import uuid
from pathlib import Path
from games import services as games
from games.tests.helpers import make_session, CHIP_STAKES
from groups.models import Member
from ledger import services as ledger
host = Member.objects.get(user__username='hana', role='host')
members = list(Member.objects.filter(group=host.group, user__isnull=True).order_by('pk')[:2])
manifest = {}
for key, unit in [('default', 'php'), ('opt_out', 'php'), ('chips', 'chips'), ('live', 'php')]:
    session = make_session(host, state='open', table_name='Opening ' + key, unit=unit,
                           **(CHIP_STAKES if unit == 'chips' else {}))
    players = games.add_participants(session.pk, host, [m.pk for m in members], uuid.uuid4())
    if key == 'default':
        ledger.record_buy_in(session.pk, host, players[0].pk, 50000, uuid.uuid4())
    manifest[key] = {'set': session.pk, 'night': session.night_id}
Path('/private/tmp/pn-opening-manifest.json').write_text(json.dumps(manifest))
