"""A final set of six players, ranked out of join order, for results.mjs. Run after seed.py on a fresh temporary DB."""
import json
import uuid
from pathlib import Path
from games import services as games
from games.tests.helpers import make_session
from groups import services as groups
from groups.models import Member
from ledger import services as ledger
from settlement import services as settlement

host = Member.objects.get(user__username='hana', role='host')
u = uuid.uuid4
names = ['Cara', 'Alexandra de la Cruz with a very long name', 'Dino', 'Elle', 'Finn', 'Gabe']
nets = [-50000, 90000, 0, -80000, 60000, -20000]
members = [groups.add_roster_player(host, name) for name in names]
s = make_session(host, state='open', table_name='six')
ps = games.add_participants(s.pk, host, [m.pk for m in members], u())
for p in ps: ledger.record_buy_in(s.pk, host, p.pk, 100000, u())
games.transition(s.pk, host, 'start')
games.transition(s.pk, host, 'end')
for p, net in zip(ps, nets): ledger.record_cash_out(s.pk, host, p.pk, 100000 + net, u())
settlement.finalize(s.pk, host)
Path('/private/tmp/pn-results-manifest.json').write_text(json.dumps({'set': s.pk, 'night': s.night_id}))
