"""Run after seed.py on a fresh temporary database. Separate counter fixtures."""
import json, uuid
from pathlib import Path
from groups.models import Member
from games.tests.helpers import make_session, CHIP_STAKES
from games import services as games
from ledger import services as ledger
host = Member.objects.get(user__username='hana', role='host')
roster = list(Member.objects.filter(group=host.group, user__isnull=True).order_by('pk')[:2])
manifest = {}
for unit in ['php', 'chips']:
    s = make_session(host, state='open', table_name='Live stack check ' + unit, unit=unit, **(CHIP_STAKES if unit == 'chips' else {}))
    ps = games.add_participants(s.pk, host, [p.pk for p in roster], uuid.uuid4())
    for p in ps:
        ledger.record_buy_in(s.pk, host, p.pk, 1000 if unit == 'chips' else 100000, uuid.uuid4())
    games.transition(s.pk, host, 'start')
    ledger.record_cash_out(s.pk, host, ps[0].pk, 100 if unit == 'chips' else 10000, uuid.uuid4())
    games.transition(s.pk, host, 'end')
    ledger.confirm_count(s.pk, host, ps[0].pk, 900 if unit == 'chips' else 90000, uuid.uuid4())
    manifest[unit] = s.pk
Path('/private/tmp/pn-counts-manifest.json').write_text(json.dumps(manifest))
print(manifest)
