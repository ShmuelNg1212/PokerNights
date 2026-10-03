from games import services

STAKES = {
    "small_blind": 1000,
    "big_blind": 2000,
    "min_buy_in": 50000,
    "max_buy_in": 200000,
    "default_buy_in": 100000,
}


def make_preset(host, name="10/20", **overrides):
    """₱10/₱20, buy-in ₱500 to ₱2,000, usual buy-in ₱1,000."""
    return services.save_preset(host, {"name": name, "game_type": "nlh", **STAKES, **overrides})


def make_table(host, name="Friday table", seat_count=9, preset=None):
    return services.create_table(host, name, seat_count, preset.pk if preset else None)


def make_session(host, *, table=None, state="setup", seat_count=9, **overrides):
    """A session with the standard stakes, moved to ``state`` through the real transitions."""
    import datetime

    table = table or make_table(host, name=overrides.pop("table_name", "Friday table"), seat_count=seat_count)
    data = {
        "table_id": table.pk, "game_date": datetime.date(2026, 10, 9), "location": "Miguel's place",
        "game_type": "nlh", **STAKES, **overrides,
    }
    session = services.create_session(host, data)
    path = {"setup": [], "open": ["open"], "running": ["open", "start"], "reconciliation": ["open", "start", "end"]}
    for action in path[state]:
        session = services.transition(session.pk, host, action)
    return session
