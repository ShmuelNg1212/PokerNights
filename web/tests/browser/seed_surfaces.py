"""First-time states for surfaces.mjs. Run after seed.py, once, on a fresh temporary database."""
import json
from pathlib import Path
from django.contrib.auth import get_user_model
from groups import services as groups
from groups.models import Member
User = get_user_model()
User.objects.create_user("nora", password="tablestakes-91")
owen = groups.create_group(User.objects.create_user("owen", password="tablestakes-91"), "Empty Table Club")
Member.objects.create(group=owen.group, user=User.objects.create_user("pia", password="tablestakes-91"), display_name="Pia")
Path('/private/tmp/pn-surfaces-manifest.json').write_text(json.dumps({'group': owen.group.pk}))
