"""Fresh temporary database only. A group with no chip presets, sessions without chip values, and logins."""
import json
from pathlib import Path
from games.tests.helpers import make_session
from ledger.tests.helpers import Night

n = Night('A')
n.add_login_player('ben')
n.buy('A', 1000)
n.buy('ben', 1000)
n.go('reconciliation')
native = make_session(n.host, state='open', table_name='No script table')
chips = make_session(n.host, state='open', table_name='Chips unit', unit='chips', small_blind=10, big_blind=20,
                     min_buy_in=500, max_buy_in=2000, default_buy_in=1000)
Path('/private/tmp/pn-chip-presets-manifest.json').write_text(json.dumps({
    'group': n.group.pk, 'set': n.session.pk, 'night': n.session.night_id, 'player': n.players['ben'].pk,
    'native': native.night_id, 'chips': chips.night_id,
}))
print('Chip preset fixtures ready.')
