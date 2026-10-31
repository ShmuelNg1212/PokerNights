"""An idle group with a preset, for journey.mjs's repeat game. Run after the other seeds it names."""
from django.contrib.auth import get_user_model
from games import services as games
from groups import services as groups
rena = get_user_model().objects.create_user("rena", password="tablestakes-91")
host = groups.create_group(rena, "Repeat crew")
for name in ["Ana", "Bong", "Ces", "Don"]:
    groups.add_roster_player(host, name)
table = games.create_table(host, "Kitchen", 9)
games.save_preset(host, {"name": "Usual", "game_type": "nlh", "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 500000, "default_buy_in": 100000})
# An earlier session, archived: this person has played before, and the group is idle.
import datetime
earlier = games.create_session(host, {"table_id": table.pk, "game_date": datetime.date(2026, 10, 1), "game_type": "nlh", "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 500000, "default_buy_in": 100000})
games.transition(earlier.pk, host, "cancel")
games.archive_night(earlier.night_id, host)
print("JOURNEY ready")
