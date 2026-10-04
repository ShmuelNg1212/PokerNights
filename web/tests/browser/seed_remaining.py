"""Extra synthetic states for the remaining Rack screens; temporary DB only."""
import json
from django.contrib.auth import get_user_model
from django.utils import timezone
from groups.models import Member
from groups import services as groups
from games import services as games
from games.models import GameSession
host = Member.objects.get(user__username='hana', role='host')
games.save_preset(host, {'name':'Usual pesos', 'game_type':'nlh', 'unit':'php', 'small_blind':1000,'big_blind':2000,'min_buy_in':50000,'max_buy_in':500000,'default_buy_in':100000})
games.save_preset(host, {'name':'Usual chips', 'game_type':'nlh', 'unit':'chips', 'small_blind':10,'big_blind':20,'min_buy_in':500,'max_buy_in':5000,'default_buy_in':1000})
get_user_model().objects.create_user('unattached',password='tablestakes-91')
empty_user=get_user_model().objects.create_user('empty-user',password='tablestakes-91')
empty_host=groups.create_group(empty_user,'A new group')
table=games.create_table(host,'Canceled table',9)
s=games.create_session(host,{'table_id':table.pk,'game_date':timezone.localdate(),'location':'','game_type':'nlh','small_blind':1000,'big_blind':2000,'min_buy_in':50000,'max_buy_in':500000,'default_buy_in':100000})
games.transition(s.pk,host,'cancel','The game was postponed.')
with open('/private/tmp/pn-slice4-manifest.json','w') as f:json.dump({'canceled':s.pk,'empty_group':empty_host.group_id},f)

import uuid,json
from groups.models import Member
from games.tests.helpers import make_session
from games import services as games
from ledger import services as ledger
from settlement import services as settlement
host=Member.objects.get(user__username='hana',role='host')
s=make_session(host,table_name='Long records',state='open',max_buy_in=100000000000)
ids=list(Member.objects.filter(group=host.group,display_name__startswith='Alex').values_list('pk',flat=True))[:2]
p=games.add_participants(s.pk,host,ids,uuid.uuid4())
b=ledger.record_buy_in(s.pk,host,p[0].pk,99999999999,uuid.uuid4())
ledger.reverse_buy_in(s.pk,host,b.pk,'Recorded at the wrong table')
for one in p:ledger.record_buy_in(s.pk,host,one.pk,99999999999,uuid.uuid4())
games.transition(s.pk,host,'start');games.transition(s.pk,host,'end')
for one in p:ledger.record_cash_out(s.pk,host,one.pk,99999999999,uuid.uuid4())
settlement.finalize(s.pk,host)
path='/private/tmp/pn-slice4-manifest.json'
with open(path) as f:data=json.load(f)
data['long_log']=s.pk
with open(path,'w') as f:json.dump(data,f)
