"""Slice 3 synthetic sessions. Run after the earlier seeds on a fresh temporary DB."""
import json
import uuid
from pathlib import Path
from games import services as games
from games.tests.helpers import make_session, CHIP_STAKES
from groups import services as groups
from groups.models import Member
from ledger import services as ledger
from settlement import services as settlement
from settlement.models import Transfer

host = Member.objects.get(user__username='hana', role='host')
ben = Member.objects.get(user__username='ben', group=host.group)
roster = list(Member.objects.filter(group=host.group, user__isnull=True).order_by('pk')[:2])
u = uuid.uuid4
manifest = {'partly': 1, 'blocked': 3, 'empty': 4}


def final(name, nets, *, unit='php', large=False, close=True):
    stakes = CHIP_STAKES if unit == 'chips' else {}
    members = [ben] + roster
    if large:
        stakes = {'min_buy_in': 100, 'max_buy_in': 9999999999, 'default_buy_in': 9999999999}
        members = [groups.add_roster_player(host, n) for n in ['Alexandra de la Cruz with a very long name', 'Benjamin Santos with a very long name', 'Beatriz Santos with a very long name']]
    s = make_session(host, state='open', table_name=name, unit=unit, **stakes)
    ps = games.add_participants(s.pk, host, [m.pk for m in members], u())
    bought = 9999999999 if large else (1000 if unit == 'chips' else 100000)
    for p in ps: ledger.record_buy_in(s.pk, host, p.pk, bought, u())
    games.transition(s.pk, host, 'start')
    games.transition(s.pk, host, 'end')
    for p, net in zip(ps, nets): ledger.record_cash_out(s.pk, host, p.pk, bought + net, u())
    settlement.finalize(s.pk, host)
    if close: settlement.close_night(s.night_id, host)
    manifest[name] = s.night_id
    return s

final('unpaid', [60000, -40000, -20000])
settled = final('settled', [60000, -40000, -20000])
for t in Transfer.objects.filter(plan__night_id=settled.night_id): settlement.mark_paid(settled.night_id, host, t.pk, u())
final('break-even', [0, 0, 0], unit='chips')
final('large', [19999999998, -9999999999, -9999999999], large=True)
final('ready', [60000, -40000, -20000], close=False)
final('next-ready', [60000, -40000, -20000], close=False)
final('tied', [30000, 30000, -60000])
Path('/private/tmp/pn-slice3-manifest.json').write_text(json.dumps(manifest))
print('NIGHT_IDS', manifest)
