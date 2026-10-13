"""Two presets for session_setup.mjs. Run after seed.py on a fresh temporary SQLite database."""
from games import services as games
from groups.models import Member
host = Member.objects.get(user__username="hana")
games.save_preset(host, {"name": "10/20", "game_type": "nlh", "small_blind": 1000, "big_blind": 2000, "min_buy_in": 50000, "max_buy_in": 200000, "default_buy_in": 100000})
games.save_preset(host, {"name": "Chips 25/50 deep", "game_type": "nlh", "unit": "chips", "small_blind": 25, "big_blind": 50, "min_buy_in": 1000000, "max_buy_in": 5000000, "default_buy_in": 2000000})
