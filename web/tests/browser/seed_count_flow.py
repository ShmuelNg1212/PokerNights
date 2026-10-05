"""Run after seed.py on a fresh temporary database. Count-up sets for count_flow.mjs: eight players, and the end states."""
import json, uuid
from pathlib import Path
from groups.models import Member
from games.tests.helpers import make_session, CHIP_STAKES
from games import services as games
from ledger import services as ledger
host = Member.objects.get(user__username='hana', role='host')
ben = Member.objects.get(user__username='ben')
roster = list(Member.objects.filter(group=host.group, user__isnull=True).order_by('pk')[:7])
u = uuid.uuid4
manifest = {}
def counting(name, members, unit='php', buy=None):
    s = make_session(host, state='open', table_name=name, unit=unit, **(CHIP_STAKES if unit == 'chips' else {}))
    ps = games.add_participants(s.pk, host, [m.pk for m in members], u())
    for p in ps:
        ledger.record_buy_in(s.pk, host, p.pk, buy if buy is not None else (1000 if unit == 'chips' else 100000), u())
    games.transition(s.pk, host, 'start')
    return s, ps
# Eight players, nobody counted. One rebuy and one earlier partial cash-out.
for unit in ('php', 'chips'):
    one = 1000 if unit == 'chips' else 100000
    s, ps = counting('Eight ' + unit, roster + [ben], unit)
    ledger.record_buy_in(s.pk, host, ps[1].pk, one, u())
    ledger.record_cash_out(s.pk, host, ps[0].pk, one // 10, u())
    games.transition(s.pk, host, 'end')
    manifest['eight' if unit == 'php' else 'chips'] = s.pk
# Everyone cashed out: balanced, off by 100 pesos, and off with an override.
for key, last in (('balanced', 100000), ('off', 90000), ('override', 90000)):
    s, ps = counting('Books ' + key, roster[:2])
    games.transition(s.pk, host, 'end')
    ledger.record_cash_out(s.pk, host, ps[0].pk, 100000, u())
    ledger.record_cash_out(s.pk, host, ps[1].pk, last, u())
    if key == 'override':
        ledger.record_override(s.pk, host, 'Synthetic recount', 'player', ps[0].pk, u())
    manifest[key] = s.pk
# Two players, nobody counted: walked from counts to a finalized set.
s, ps = counting('Books finish', roster[:2])
games.transition(s.pk, host, 'end')
manifest['finish'] = s.pk
# No buy-in at all.
s = make_session(host, state='open', table_name='Books empty')
games.add_participants(s.pk, host, [m.pk for m in roster[:2]], u())
games.transition(s.pk, host, 'start', opening_buy_ins=False)
games.transition(s.pk, host, 'end')
manifest['empty'] = s.pk
Path('/private/tmp/pn-count-flow-manifest.json').write_text(json.dumps(manifest))
print(manifest)
