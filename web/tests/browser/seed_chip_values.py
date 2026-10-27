"""Fresh temporary database only. Synthetic chip-count sessions and logins."""
import json
import uuid
from pathlib import Path
from games import services as games
from games.tests.helpers import make_session
from ledger.tests.helpers import Night
from ledger import services as ledger

n = Night('A')
player = n.add_login_player('ben')
n.buy('A', 1000)
n.buy('ben', 1000)
n.go('reconciliation')
values = [{'colour': 'white', 'label': '', 'value': 500},
          {'colour': 'red', 'label': 'Small', 'value': 2500},
          {'colour': 'green', 'label': '', 'value': 10000}]
games.set_chip_values(n.session.night_id, n.host, values, uuid.uuid4(), revision=0)
other = make_session(n.host, state='open', table_name='Different values')
games.set_chip_values(other.night_id, n.host, [{'colour': 'red', 'label': 'Other red', 'value': 5000}], uuid.uuid4(), revision=0)
setup = make_session(n.host, state='open', table_name='Set up colours')
chips = make_session(n.host, state='open', table_name='Chips unit', unit='chips', small_blind=10, big_blind=20,
                     min_buy_in=500, max_buy_in=2000, default_buy_in=1000)
games.set_chip_values(chips.night_id, n.host, [{'colour': 'red', 'label': '', 'value': 25}], uuid.uuid4(), revision=0)
second = games.start_next_set(n.session.night_id, n.host)
second = games.transition(second.pk, n.host, 'start', opening_buy_ins=True)
second = games.transition(second.pk, n.host, 'end')
stale = make_session(n.host, state='open', table_name='Stale draft check')
sp = games.add_participant(stale.pk, n.host, player.pk)
ledger.record_buy_in(stale.pk, n.host, sp.pk, 100000, uuid.uuid4())
games.transition(stale.pk, n.host, 'start', opening_buy_ins=False)
games.transition(stale.pk, n.host, 'end')
games.set_chip_values(stale.night_id, n.host, values, uuid.uuid4(), revision=0)
Path('/private/tmp/pn-chip-manifest.json').write_text(json.dumps({
    'set': n.session.pk, 'night': n.session.night_id, 'player': n.players['ben'].pk, 'a': n.players['A'].pk,
    'other': other.night_id, 'setup': setup.night_id, 'chips': chips.night_id, 'second': second.pk,
    'second_player': second.participants.get(member=player).pk, 'stale': stale.pk, 'stale_night': stale.night_id, 'stale_player': sp.pk,
}))
print('Chip fixtures ready.')
