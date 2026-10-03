"""Read-only totals. Nothing here is stored: each figure is calculated from the records."""

from dataclasses import dataclass, field

from games.models import GameSession, Participant

from .models import BuyIn


@dataclass
class PlayerLine:
    """One participant's money in a session."""

    participant: Participant
    buy_ins: list = field(default_factory=list)  # accepted, oldest first
    reversed_buy_ins: list = field(default_factory=list)

    @property
    def buy_in_count(self) -> int:
        return len(self.buy_ins)

    @property
    def rebuy_count(self) -> int:
        """Every accepted buy-in after the first."""
        return max(self.buy_in_count - 1, 0)

    @property
    def initial_buy_in(self):
        return self.buy_ins[0] if self.buy_ins else None

    @property
    def buy_in_total(self) -> int:
        return sum(b.amount_centavos for b in self.buy_ins)

    @property
    def chips_issued(self) -> int:
        return sum(b.chips for b in self.buy_ins)

    @property
    def has_money(self) -> bool:
        return bool(self.buy_ins)


@dataclass
class Summary:
    session: GameSession
    lines: list

    @property
    def player_count(self) -> int:
        return len(self.lines)

    @property
    def buy_in_count(self) -> int:
        return sum(line.buy_in_count for line in self.lines)

    @property
    def total_centavos(self) -> int:
        """Total pesos bought in: the sum of the recorded amounts of accepted buy-ins."""
        return sum(line.buy_in_total for line in self.lines)

    @property
    def chips_issued(self) -> int:
        return sum(line.chips_issued for line in self.lines)

    def line_for(self, participant_id):
        return next((line for line in self.lines if line.participant.pk == participant_id), None)


def summary(session: GameSession) -> Summary:
    """Every participant who is in the session or has money in it, in join order."""
    lines = {
        p.pk: PlayerLine(p)
        for p in Participant.objects.filter(session=session).select_related("member").order_by("join_order")
    }
    for buy_in in BuyIn.objects.filter(session=session).select_related("reversal", "recorded_by"):
        line = lines[buy_in.participant_id]
        if hasattr(buy_in, "reversal"):
            line.reversed_buy_ins.append(buy_in)
        else:
            line.buy_ins.append(buy_in)
    shown = [
        line for line in lines.values()
        if line.participant.status != Participant.Status.WITHDRAWN or line.has_money
    ]
    return Summary(session, shown)
