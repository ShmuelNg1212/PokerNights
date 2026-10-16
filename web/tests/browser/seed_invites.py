"""Fixture for invites.mjs. Run only on a fresh temporary SQLite database; it needs no other seed.

Host ``hana`` with a group that has one link that can be shown, one made before links could be shown,
and past invites that were revoked, expired and used up.
"""
import json
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from groups import services as groups
from groups.models import Invite
User = get_user_model()
host = groups.create_group(User.objects.create_user("hana", password="tablestakes-91"), "Kamuning Friday Night Card Club")
now = timezone.now()
for change in ({"revoked_at": now - timedelta(days=9)}, {"expires_at": now - timedelta(days=3)}, {"use_count": 20}):
    invite = groups.create_invite(host)[0]
    Invite.objects.filter(pk=invite.pk).update(**change)
old = groups.create_invite(host)[0]
Invite.objects.filter(pk=old.pk).update(salt=None, use_count=4)
shown, token = groups.create_invite(host)
with open("/private/tmp/pn-invites-manifest.json", "w") as out:
    json.dump({"group": host.group_id, "shown": shown.pk, "token": token, "old": old.pk}, out)
print("invites fixture ready")
