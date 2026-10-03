from games import services

STAKES = {
    "small_blind_centavos": 1000,
    "big_blind_centavos": 2000,
    "min_buy_in_centavos": 50000,
    "max_buy_in_centavos": 200000,
    "default_buy_in_centavos": 100000,
    "chips_per_buy_in": 10000,
}


def make_preset(host, name="10/20", **overrides):
    """₱10/₱20, buy-in ₱500 to ₱2,000, and ₱1,000 buys 10,000 chips."""
    return services.save_preset(host, {"name": name, "game_type": "nlh", **STAKES, **overrides})


def make_table(host, name="Friday table", seat_count=9, preset=None):
    return services.create_table(host, name, seat_count, preset.pk if preset else None)
