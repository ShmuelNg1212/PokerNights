"""Independent synthetic rake fixtures; use a fresh temporary database."""
import json, uuid
from pathlib import Path
from groups.tests.helpers import make_group, add_player
from groups.models import Member
from games import services as games
from games.tests.helpers import make_session, CHIP_STAKES
from ledger import services as ledger
host = make_group()[1]
ben = add_player(host.group, 'ben', role=Member.Role.HOST)
ids = {'group':host.group_id}
for name, unit in [('percent','php'), ('flat','chips'), ('off','php'), ('count','php'), ('percentchips','chips'), ('flatphp','php')]:
    s = make_session(host, state='open', table_name='Rake '+name, unit=unit, **(CHIP_STAKES if unit=='chips' else {}))
    games.add_participants(s.pk, host, [host.pk, ben.pk], uuid.uuid4())
    ids[name] = s.pk
    if name == 'count':
        games.update_settings(s.pk, host, {**games.current_settings(s).stakes(), 'rake_mode':'percent','rake_basis_points':500}, request_id=uuid.uuid4())
        games.transition(s.pk, host, 'start')
        games.transition(s.pk, host, 'end')
Path('/private/tmp/pn-rake-manifest.json').write_text(json.dumps(ids))
print(ids)
