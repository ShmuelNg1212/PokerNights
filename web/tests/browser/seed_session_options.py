"""Fresh temporary database only. A group with a table, a stakes preset, chip presets of both units, and a player login."""
import json
import uuid
from pathlib import Path

from games import services
from games.tests.helpers import make_preset, make_table
from groups.tests.helpers import add_player, make_group

group, host = make_group('hana', 'Options group')
add_player(group, 'ben')
make_table(host, preset=make_preset(host))
for name, unit, value in (('Home set', 'php', 2500), ('Tournament set', 'chips', 25)):
    services.save_chip_preset(host, {'name': name, 'unit': unit, 'values': [{'colour': 'red', 'value': value}]}, uuid.uuid4())
Path('/private/tmp/pn-session-options-manifest.json').write_text(json.dumps({'group': group.pk}))
print('Session option fixtures ready.')
