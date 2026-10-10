"""Run after seed.py on a fresh temporary DB. Sets for pot.mjs (the pot's figure when its amount changes)."""
import json
import uuid
from pathlib import Path
from games import services as games
from games.tests.helpers import make_session, CHIP_STAKES
from groups.models import Member
from ledger import services as ledger
host = Member.objects.get(user__username='hana', role='host')
roster = list(Member.objects.filter(group=host.group, user__isnull=True).order_by('pk'))
manifest = {}
def table(key, amounts, unit='php', **stakes):
    session = make_session(host, state='open', table_name='Pot ' + key, unit=unit, **stakes)
    players = games.add_participants(session.pk, host, [m.pk for m in roster[:len(amounts)]], uuid.uuid4())
    for p, amount in zip(players, amounts): ledger.record_buy_in(session.pk, host, p.pk, amount, uuid.uuid4())
    games.transition(session.pk, host, 'start', opening_buy_ins=False)
    manifest[key] = {'set': session.pk, 'players': [p.pk for p in players]}
# ₱4,000 in play; "grow" stands at ₱9,500; "chips" at 4,000 chips.
for key in ('roll', 'desk', 'still', 'plain', 'guard'): table(key, [100000] * 4)
table('grow', [500000, 450000], max_buy_in=100000000)
table('chips', [1000] * 4, unit='chips', **CHIP_STAKES)
Path('/private/tmp/pn-pot-manifest.json').write_text(json.dumps(manifest))
print('POT', manifest)
