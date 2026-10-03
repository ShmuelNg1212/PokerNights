import uuid

from games import services as games
from games.tests.helpers import make_session
from groups import services as groups
from groups.tests.helpers import add_player, make_group
from ledger import services


class Night:
    """A session with a host and named players, for tests. ₱1,000 buys 10,000 chips."""

    def __init__(self, *names, state="running", seat_count=9, **stakes):
        self.group, self.host = make_group()
        self.session = make_session(self.host, state="open", seat_count=seat_count, **stakes)
        self.players = {}
        for name in names:
            member = groups.add_roster_player(self.host, name)
            self.players[name] = games.add_participant(self.session.pk, self.host, member.pk)
        self.go(state)

    def go(self, state):
        """Move forward to ``state`` from wherever the session is now."""
        order = ["open", "running", "reconciliation"]
        actions = ["start", "end"]
        for action in actions[order.index(self.session.state):order.index(state)]:
            self.session = games.transition(self.session.pk, self.host, action)

    def add_login_player(self, name):
        member = add_player(self.group, name)
        self.players[name] = games.add_participant(self.session.pk, self.host, member.pk)
        return member

    def buy(self, name, pesos, request_id=None):
        return services.record_buy_in(
            self.session.pk, self.host, self.players[name].pk, pesos * 100, request_id or uuid.uuid4()
        )

    def refresh(self):
        self.session.refresh_from_db()
        return self.session

    def cash(self, name, chips, request_id=None, left=False):
        return services.record_cash_out(
            self.session.pk, self.host, self.players[name].pk, chips, request_id or uuid.uuid4(), left=left
        )

    def line(self, name):
        from ledger import queries

        return queries.summary(self.session).line_for(self.players[name].pk)
