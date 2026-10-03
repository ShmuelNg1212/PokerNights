"""Read-only totals. Nothing here is stored: each figure is calculated from the records."""

from dataclasses import dataclass, field

from games.models import GameSession, Participant

from . import money
from .models import BalanceAdjustment, BuyIn, CashOut


@dataclass
class PlayerLine:
    """One participant's money in a session."""

    participant: Participant
    buy_ins: list = field(default_factory=list)  # accepted, oldest first
    reversed_buy_ins: list = field(default_factory=list)
    cash_outs: list = field(default_factory=list)  # accepted, oldest first
    reversed_cash_outs: list = field(default_factory=list)
    adjustments: list = field(default_factory=list)  # active (not voided)

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

    @property
    def has_cash_out(self) -> bool:
        """True once any cash-out is recorded, including a cash-out of zero chips."""
        return bool(self.cash_outs)

    @property
    def chips_cashed(self) -> int:
        return sum(c.chips for c in self.cash_outs)

    @property
    def adjustment_chips(self) -> int:
        return sum(a.chips_delta for a in self.adjustments)

    @property
    def chips_final(self) -> int:
        """Chips this player is paid for: cashed-out chips plus any host adjustment."""
        return self.chips_cashed + self.adjustment_chips

    @property
    def cash_value(self):
        """``(centavos rounded down, exact?)`` for the chips cashed so far, or None without a rate.

        The final value is fixed at finalization, where centavo remainders are shared out.
        """
        rate = self.participant.session.rate
        return money.value_floor(self.chips_cashed, rate) if rate else None


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

    @property
    def chips_cashed(self) -> int:
        return sum(line.chips_cashed for line in self.lines)

    @property
    def chips_in_play(self) -> int:
        """Chips issued that have not been cashed out. Not a peso amount."""
        return self.chips_issued - self.chips_cashed

    @property
    def adjustment_chips(self) -> int:
        return sum(line.adjustment_chips for line in self.lines)

    @property
    def money_lines(self) -> list:
        """Players with an accepted buy-in, in join order. These are the players who get a result."""
        return [line for line in self.lines if line.has_money]

    def line_for(self, participant_id):
        return next((line for line in self.lines if line.participant.pk == participant_id), None)


def summary(session: GameSession) -> Summary:
    """Every participant who is in the session or has money in it, in join order."""
    lines = {
        p.pk: PlayerLine(p)
        for p in Participant.objects.filter(session=session).select_related("member", "session").order_by("join_order")
    }
    for buy_in in BuyIn.objects.filter(session=session).select_related("reversal", "recorded_by"):
        line = lines[buy_in.participant_id]
        if hasattr(buy_in, "reversal"):
            line.reversed_buy_ins.append(buy_in)
        else:
            line.buy_ins.append(buy_in)
    for cash_out in CashOut.objects.filter(session=session).select_related("reversal", "recorded_by"):
        line = lines[cash_out.participant_id]
        if hasattr(cash_out, "reversal"):
            line.reversed_cash_outs.append(cash_out)
        else:
            line.cash_outs.append(cash_out)
    for adjustment in BalanceAdjustment.objects.filter(session=session, voided_at__isnull=True):
        lines[adjustment.participant_id].adjustments.append(adjustment)
    shown = [
        line for line in lines.values()
        if line.participant.status != Participant.Status.WITHDRAWN or line.has_money or line.has_cash_out
    ]
    return Summary(session, shown)


@dataclass
class Balance:
    """The balance check: do the chips handed in match the chips issued?"""

    summary: Summary
    missing_cash_outs: list  # players with buy-ins and no cash-out record
    stray_cash_outs: list  # players with a cash-out and no accepted buy-in
    raw_difference: int  # chips cashed − chips issued, before adjustments
    difference: int  # the same, after active adjustments

    @property
    def counted(self) -> bool:
        """Every player's chips are recorded, so the difference is meaningful."""
        return bool(self.summary.money_lines) and not self.missing_cash_outs and not self.stray_cash_outs

    @property
    def ok(self) -> bool:
        return self.counted and self.difference == 0

    @property
    def overridden(self) -> bool:
        return self.ok and self.raw_difference != 0

    @property
    def direction(self) -> str:
        """``extra`` chips (more handed in than issued), ``missing`` chips, or empty."""
        if self.difference > 0:
            return "extra"
        return "missing" if self.difference < 0 else ""

    def _value(self, chips) -> str:
        rate = self.summary.session.rate
        if rate is None:
            return ""
        value, exact = money.value_floor(abs(chips), rate)
        return f"{'' if exact else 'about '}{money.format_pesos(value)}"

    @property
    def difference_value(self) -> str:
        return self._value(self.difference)

    @property
    def raw_difference_value(self) -> str:
        return self._value(self.raw_difference)

    @property
    def explanation(self) -> str:
        """What is wrong and where to look. Empty when the books balance."""
        if not self.summary.money_lines:
            return "No buy-in is recorded, so there is nothing to finalize."
        if self.stray_cash_outs:
            names = ", ".join(line.participant.member.display_name for line in self.stray_cash_outs)
            return f"{names} cashed out chips but has no buy-in. Record the buy-in, or reverse the cash-out."
        if self.missing_cash_outs:
            names = ", ".join(line.participant.member.display_name for line in self.missing_cash_outs)
            return f"No cash-out is recorded for: {names}. Record each player's chips. Enter 0 for a player who lost everything."
        chips = f"{abs(self.difference):,} chips ({self.difference_value})"
        if self.difference > 0:
            return (
                f"There are {chips} extra: more chips were cashed out than were issued. "
                "Look for a buy-in that was not recorded, or a chip count that is too high."
            )
        if self.difference < 0:
            return (
                f"There are {chips} missing: fewer chips were cashed out than were issued. "
                "Look for chips that were not counted, a buy-in recorded twice, or a chip count that is too low."
            )
        return ""


def balance(session_or_summary) -> Balance:
    found = session_or_summary if isinstance(session_or_summary, Summary) else summary(session_or_summary)
    return Balance(
        summary=found,
        missing_cash_outs=[line for line in found.lines if line.has_money and not line.has_cash_out],
        stray_cash_outs=[line for line in found.lines if line.has_cash_out and not line.has_money],
        raw_difference=found.chips_cashed - found.chips_issued,
        difference=found.chips_cashed + found.adjustment_chips - found.chips_issued,
    )
