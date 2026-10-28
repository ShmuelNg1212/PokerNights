"""Fresh temporary database only. A twelve-colour chip count and an empty setup page, for the app's number keys."""
import json
import uuid
from pathlib import Path
from games import chips
from games import services as games
from games.tests.helpers import make_session
from ledger.tests.helpers import Night

n = Night('A')
n.add_login_player('ben')
n.buy('A', 1000)
n.buy('ben', 1000)
n.go('reconciliation')
values = [{'colour': key, 'label': '', 'value': (i + 1) * 100} for i, (key, _, _) in enumerate(chips.COLOURS)]
games.set_chip_values(n.session.night_id, n.host, values, uuid.uuid4(), revision=0)
setup = make_session(n.host, state='open', table_name='Set up colours')
Path('/private/tmp/pn-chip-numpad-manifest.json').write_text(json.dumps({
    'set': n.session.pk, 'player': n.players['ben'].pk, 'setup': setup.night_id,
}))
print('Chip numpad fixtures ready.')
