"""Run after seed.py on a fresh temporary DB. Invite links for the entry pages."""
import json
from pathlib import Path
from django.utils import timezone
from groups import services as groups
from groups.models import Member
host = Member.objects.get(user__username='hana', role='host')
_, token = groups.create_invite(host)
long = groups.create_group(host.user, 'TheVeryLongUnbrokenGroupNameThatMustWrapInsideItsContainerX')
_, long_token = groups.create_invite(long)
expired, expired_token = groups.create_invite(host)
expired.expires_at = timezone.now()
expired.save(update_fields=['expires_at'])
from accounts.models import User
User.objects.create_user('visitor', password='tablestakes-91')
manifest = {'group': host.group.name, 'invite': f'/join/{token}/', 'long': f'/join/{long_token}/', 'expired': f'/join/{expired_token}/'}
Path('/private/tmp/pn-entry-manifest.json').write_text(json.dumps(manifest))
print(manifest)
