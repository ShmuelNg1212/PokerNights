"""Fixture for chat_browser.mjs. Run only on a fresh temporary SQLite database; it needs no other seed.

Host ``hana`` with one group, a live invite and a long group name, so the card is checked beside the longest heading.
"""
import json
from django.contrib.auth import get_user_model
from groups import services as groups
User = get_user_model()
host = groups.create_group(User.objects.create_user("hana", password="tablestakes-91"), "Kamuning Friday Night Card Club")
token = groups.create_invite(host)[1]
with open("/private/tmp/pn-chat-manifest.json", "w") as out:
    json.dump({"join": f"/join/{token}/"}, out)
print("chat browser fixture ready")
