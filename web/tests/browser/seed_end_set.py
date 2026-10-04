"""Add slice 2 states after seed.py, once, on a fresh synthetic database."""
import uuid
from django.utils import timezone
from games import services as games
from games.tests.helpers import make_session, CHIP_STAKES
from groups import services as groups
from groups.models import Member
from ledger import services as ledger
from ledger.models import FinalCount
host = Member.objects.get(user__username='hana', role='host')
roster = list(Member.objects.filter(group=host.group, user__isnull=True).order_by('pk')[:2])
u = uuid.uuid4

def counting(name, *, unit='php', empty=False, large=False):
    stakes = CHIP_STAKES if unit == 'chips' else {}
    if large:
        stakes = {'min_buy_in': 100, 'max_buy_in': 10000000000, 'default_buy_in': 100000000}
    s = make_session(host, state='open', table_name=name, unit=unit, **stakes)
    members = roster
    if large:
        members = [groups.add_roster_player(host, 'AlexandriaDeLaCruzWithAVeryLongUnbrokenDisplayName'),
                   groups.add_roster_player(host, 'Benjamin Santos with a longer name')]
    ps = games.add_participants(s.pk, host, [p.pk for p in members], u())
    if not empty:
        for p in ps: ledger.record_buy_in(s.pk, host, p.pk, 1000 if unit == 'chips' else (9999999999 if large else 100000), u())
    games.transition(s.pk, host, 'start', opening_buy_ins=not empty)
    if not empty and not large: ledger.record_cash_out(s.pk, host, ps[0].pk, 100 if unit == 'chips' else 10000, u())
    games.transition(s.pk, host, 'end')
    return s, ps

chips, cp = counting('Chips counting', unit='chips')  # 6
ledger.confirm_counts(chips.pk, host, {cp[0].pk: 1900, cp[1].pk: 0}, u())
empty, _ = counting('No money yet', empty=True)  # 7
for name, final, override in [('Balanced books', 100000, False), ('Recount needed', 90000, False), ('Host override', 90000, True)]:
    s, ps = counting(name)  # 8, 9, 10
    ledger.confirm_counts(s.pk, host, {ps[0].pk: 90000, ps[1].pk: final}, u())
    ledger.cash_out_counted(s.pk, host, list(FinalCount.objects.filter(session=s, is_current=True).values_list('pk',flat=True)), u())
    if override: ledger.record_override(s.pk, host, 'Synthetic recount: host absorbs missing stack', 'player', ps[0].pk, u())
large, _ = counting('Long names and large totals', large=True)  # 11
print('END_SET_IDS', chips.pk, empty.pk, large.pk)
