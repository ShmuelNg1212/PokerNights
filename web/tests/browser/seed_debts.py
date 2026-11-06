"""Synthetic debts only. Run on a fresh temporary database with DEBTS_VIEW=True."""
import json
import uuid
from pathlib import Path

from django.contrib.auth import get_user_model
from games import services as games
from games.tests.helpers import make_session
from groups import services as groups
from ledger import services as ledger
from settlement import services
from settlement.tests.test_carried import Club

User = get_user_model()
fixtures = {}
for engine in ('chromium', 'webkit'):
    club = Club('Ana', 'Ben', 'Carlo', 'Dee')
    for name, member in club.members.items():
        member.user = User.objects.create_user(engine + '-' + name.lower(), password='tablestakes-91')
        member.save(update_fields=['user'])
    nights = [club.closed({'Ana': -500, 'Ben': 500}), club.closed({'Ana': -100, 'Ben': 100}),
              club.closed({'Ana': 400, 'Ben': -400})]
    club.closed({'Carlo': -70, 'Dee': 70})
    fixtures[engine] = {'group': club.group.pk, 'host': club.host.user.username,
                        'nights': nights, 'receiver': engine + '-ben', 'payer': engine + '-ana'}

club = Club('A', 'ChristopherAlexanderMontgomeryTheThirdAndFamilyAtTheLongTable'[:60])
for i in range(19):
    name = 'J' if i == 0 else f'Player {i + 2}'
    club.members[name] = groups.add_roster_player(club.host, name)
a = club.members['A']
for index, member in enumerate(list(club.members.values())[1:]):
    session = make_session(club.host, state='open', table_name=f'Stress table {index}', max_buy_in=1000000000)
    seats = [games.add_participant(session.pk, club.host, m.pk) for m in (a, member)]
    bank = 200000000
    amount = 100000050 if index == 0 else (index + 1) * 10000
    for seat in seats:
        ledger.record_buy_in(session.pk, club.host, seat.pk, bank, uuid.uuid4())
    games.transition(session.pk, club.host, 'start', opening_buy_ins=False)
    games.transition(session.pk, club.host, 'end')
    ledger.record_cash_out(session.pk, club.host, seats[0].pk, bank - amount, uuid.uuid4())
    ledger.record_cash_out(session.pk, club.host, seats[1].pk, bank + amount, uuid.uuid4())
    services.finalize(session.pk, club.host)
    services.close_night(session.night_id, club.host)
club.closed({'A': -50, list(club.members)[1]: 50}, unit='chips')
fixtures['stress'] = {'group': club.group.pk, 'host': club.host.user.username}
Path('/private/tmp/pn-debts-manifest.json').write_text(json.dumps(fixtures))
print(json.dumps(fixtures))
