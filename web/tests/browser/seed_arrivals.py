"""On a fresh temporary DB (seed.py not needed). Fixtures for arrivals.mjs: players arriving on another
phone's set page, the "added you" line on Your groups, and the table alerts panel.

Group "Arrivals" with host ari and players with logins bea, cal and dan (password tablestakes-91),
and a roster of fourteen without a login; group "Quiet room" where ari hosts and cal plays.
"""
import json
import uuid
from pathlib import Path

from games import services as games
from games.tests.helpers import make_session
from groups import services as groups
from groups.tests.helpers import add_player, make_group

group, host = make_group('ari', 'Arrivals')
bea, cal, dan = (add_player(group, name) for name in ('bea', 'cal', 'dan'))
roster = [groups.add_roster_player(host, name) for name in
          ('Gus', 'Hal', 'Ivy', 'Jo', 'Kai', 'Lou', 'Max', 'Ned', 'Oli', 'Pia', 'Quin', 'Rex', 'Sol', 'Tam')]


def table(name, seated, state):
    session = make_session(host, state='open' if state != 'setup' else 'setup', table_name=name, seat_count=12)
    if seated:
        games.add_participants(session.pk, host, [m.pk for m in seated], uuid.uuid4())
    if state == 'running':
        games.transition(session.pk, host, 'start', opening_buy_ins=False)
    return session


manifest = {}
# 390 and 1280: bea watches a set in play with eight players; the other host adds the spares.
for key, spares in (('narrow', roster[7:10]), ('wide', roster[10:13])):
    session = table(f'Rail {key}', [bea] + roster[:7], 'running')
    manifest[key] = {'set': session.pk, 'spare': [m.pk for m in spares], 'names': [m.display_name for m in spares]}
# Reduced motion: dan watches; one spare.
session = table('Rail still', [dan] + roster[:7], 'running')
manifest['still'] = {'set': session.pk, 'spare': [roster[13].pk], 'names': [roster[13].display_name]}
# Your groups: in a second group of its own (a card shows one set), cal is in a draft the host then opens.
from groups.models import Member
home = groups.create_group(host.user, 'Quiet room')
mine = Member.objects.create(group=home.group, user=cal.user, display_name='cal', role=Member.Role.PLAYER)
draft = make_session(home, table_name='Quiet table')
games.add_participants(draft.pk, home, [mine.pk], uuid.uuid4())
manifest['draft'] = {'set': draft.pk, 'host_member': home.pk}
# The next set (2026-10-15): set 1 counting up with bea and dan holding chips, and set 1 finalized with bea.
from ledger import services as ledger
from settlement import services as settlement


def ended(name, seated, finalize):
    session = table(name, seated, 'running')
    players = list(session.participants.select_related('member').order_by('join_order'))
    for p in players[:2]:
        ledger.record_buy_in(session.pk, host, p.pk, 100000, uuid.uuid4())
    games.transition(session.pk, host, 'end')
    if finalize:
        for p in players[:2]:
            ledger.record_cash_out(session.pk, host, p.pk, 100000, uuid.uuid4())
        settlement.finalize(session.pk, host)
    return session


manifest['between'] = {'set': ended('Rail between', [bea, dan] + roster[:3], False).pk}
manifest['final'] = {'set': ended('Rail final', [bea] + roster[:3], True).pk}
Path('/private/tmp/pn-arrivals-manifest.json').write_text(json.dumps(manifest))
print('ARRIVALS', manifest)
