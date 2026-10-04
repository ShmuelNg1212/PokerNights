"""Read-only totals. Nothing here is stored: each figure is calculated from the records.

Every amount is in the session's unit (pesos or chips).
"""

from dataclasses import dataclass, field

from games.models import GameSession, Participant

from . import money
from .models import BalanceAdjustment, BuyIn, CashOut, FinalCount, RakeEntry


@dataclass
class PlayerLine:
    """One participant's money in a session."""

    participant: Participant
    buy_ins: list = field(default_factory=list)  # accepted, oldest first
    reversed_buy_ins: list = field(default_factory=list)
    cash_outs: list = field(default_factory=list)  # accepted, oldest first
    reversed_cash_outs: list = field(default_factory=list)
    adjustments: list = field(default_factory=list)  # active (not voided)
    count: object = None  # the current confirmed FinalCount, if any

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
        return sum(b.amount for b in self.buy_ins)

    @property
    def rake_total(self) -> int:
        return sum(b.rake_amount for b in self.buy_ins)

    @property
    def playable_total(self) -> int:
        return self.buy_in_total - self.rake_total

    @property
    def has_money(self) -> bool:
        return bool(self.buy_ins)

    @property
    def has_cash_out(self) -> bool:
        """True once any cash-out is recorded, including a cash-out of zero."""
        return bool(self.cash_outs)

    @property
    def is_cashed_out(self) -> bool:
        """The player has a final cash-out: nothing of theirs is left on the table."""
        return any(c.kind == CashOut.Kind.FINAL for c in self.cash_outs)

    @property
    def status(self) -> str:
        """Where the player stands at the end of a set: ``cashed_out``, ``ready`` or ``awaiting``."""
        if self.is_cashed_out:
            return "cashed_out"
        return "ready" if self.count is not None else "awaiting"

    @property
    def status_label(self) -> str:
        return {"cashed_out": "Cashed out", "ready": "Ready to cash out", "awaiting": "Awaiting count"}[self.status]

    @property
    def cashed_out(self) -> int:
        return sum(c.amount for c in self.cash_outs)

    @property
    def adjustment(self) -> int:
        return sum(a.amount for a in self.adjustments)

    @property
    def cash_out_final(self) -> int:
        """What this player's result is based on: cash-outs plus any host override."""
        return self.cashed_out + self.adjustment


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
    def total(self) -> int:
        """Total bought in: the sum of the recorded amounts of accepted buy-ins."""
        return sum(line.buy_in_total for line in self.lines)

    @property
    def rake(self) -> int:
        return sum(line.rake_total for line in self.lines)

    @property
    def playable(self) -> int:
        return self.total - self.rake

    @property
    def cashed_out(self) -> int:
        return sum(line.cashed_out for line in self.lines)

    @property
    def in_play(self) -> int:
        """Playable money not yet cashed out."""
        return self.playable - self.cashed_out

    @property
    def adjustment(self) -> int:
        return sum(line.adjustment for line in self.lines)

    @property
    def money_lines(self) -> list:
        """Players with an accepted buy-in, in join order. These are the players who get a result."""
        return [line for line in self.lines if line.has_money]

    @property
    def ready_lines(self) -> list:
        """Counted and waiting for cash-out, in join order."""
        return [line for line in self.money_lines if line.status == "ready"]

    @property
    def awaiting_lines(self) -> list:
        return [line for line in self.money_lines if line.status == "awaiting"]

    @property
    def cashed_out_lines(self) -> list:
        return [line for line in self.money_lines if line.status == "cashed_out"]

    def line_for(self, participant_id):
        return next((line for line in self.lines if line.participant.pk == participant_id), None)


def summary(session: GameSession) -> Summary:
    """Every participant who is in the session or has money in it, in join order."""
    lines = {
        p.pk: PlayerLine(p)
        for p in Participant.objects.filter(session=session).select_related("member").order_by("join_order")
    }
    for buy_in in BuyIn.objects.filter(session=session).select_related("reversal", "recorded_by", "rake_entry"):
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
    for count in FinalCount.objects.filter(session=session, is_current=True).select_related("confirmed_by"):
        lines[count.participant_id].count = count
    for adjustment in BalanceAdjustment.objects.filter(session=session, voided_at__isnull=True):
        lines[adjustment.participant_id].adjustments.append(adjustment)
    shown = [
        line for line in lines.values()
        if line.participant.status != Participant.Status.WITHDRAWN or line.has_money or line.has_cash_out
    ]
    return Summary(session, shown)


@dataclass
class Balance:
    """The balance check: do cash-outs plus rake equal gross buy-ins?"""

    summary: Summary
    missing_cash_outs: list  # players with buy-ins and no final cash-out
    stray_cash_outs: list  # players with a cash-out and no accepted buy-in
    raw_difference: int  # cashed out + rake − gross bought in, before overrides
    difference: int  # the same, after active overrides

    @property
    def counted(self) -> bool:
        """Every player's cash-out is recorded, so the difference is meaningful."""
        return bool(self.summary.money_lines) and not self.missing_cash_outs and not self.stray_cash_outs

    @property
    def ok(self) -> bool:
        return self.counted and self.difference == 0

    @property
    def overridden(self) -> bool:
        return self.ok and self.raw_difference != 0

    @property
    def direction(self) -> str:
        """``extra`` (more cashed out than bought in), ``missing``, or empty."""
        if self.difference > 0:
            return "extra"
        return "missing" if self.difference < 0 else ""

    def _show(self, value) -> str:
        return money.format_amount(abs(value), self.summary.session.unit)

    @property
    def difference_text(self) -> str:
        return self._show(self.difference)

    @property
    def raw_difference_text(self) -> str:
        return self._show(self.raw_difference)

    @property
    def explanation(self) -> str:
        """What is wrong and where to look. Empty when the books balance."""
        if not self.summary.money_lines:
            return "No buy-in is recorded, so there is nothing to finalize."
        if self.stray_cash_outs:
            names = ", ".join(line.participant.member.display_name for line in self.stray_cash_outs)
            return f"{names} has a cash-out but no buy-in. Record the buy-in, or reverse the cash-out."
        if self.missing_cash_outs:
            names = ", ".join(line.participant.member.display_name for line in self.missing_cash_outs)
            return (
                f"Not cashed out yet: {names}. Confirm each player's final count and cash them out. "
                "A count of 0 is valid for a player who lost everything."
            )
        if self.difference > 0:
            return (
                f"{self.difference_text} too much: cash-outs plus rake exceed buy-ins. "
                "Look for a buy-in that was not recorded, or a cash-out that is too high."
            )
        if self.difference < 0:
            return (
                f"{self.difference_text} is missing: cash-outs plus rake are below buy-ins. "
                "Look for a player who was not cashed out in full, a buy-in recorded twice, or a cash-out that is too low."
            )
        return ""


def balance(session_or_summary) -> Balance:
    found = session_or_summary if isinstance(session_or_summary, Summary) else summary(session_or_summary)
    return Balance(
        summary=found,
        missing_cash_outs=[line for line in found.lines if line.has_money and not line.is_cashed_out],
        stray_cash_outs=[line for line in found.lines if line.has_cash_out and not line.has_money],
        raw_difference=found.cashed_out + found.rake - found.total,
        difference=found.cashed_out + found.adjustment + found.rake - found.total,
    )


@dataclass
class CountTotal:
    """Remaining confirmed stacks plus accepted cash-outs and rake, before overrides."""

    summary: Summary

    @property
    def remaining(self) -> int:
        return sum(line.count.amount for line in self.summary.ready_lines)

    @property
    def accounted(self) -> int:
        return self.remaining + self.summary.cashed_out + self.summary.rake

    @property
    def missing(self) -> int:
        return len(self.summary.awaiting_lines)

    @property
    def stray(self) -> bool:
        return any(line.has_cash_out and not line.has_money for line in self.summary.lines)

    @property
    def has_overrides(self) -> bool:
        return any(line.adjustments for line in self.summary.lines)

    @property
    def difference(self) -> int:
        return self.accounted - self.summary.total

    @property
    def complete(self) -> bool:
        return bool(self.summary.money_lines) and not self.missing and not self.stray

    @property
    def matches(self) -> bool:
        return self.complete and self.difference == 0

    @property
    def status_text(self) -> str:
        if not self.summary.money_lines:
            return "No buy-ins recorded."
        if self.stray:
            return "Cash-out without a buy-in. Check the records."
        if self.matches:
            return "All counts match buy-ins."
        if self.difference:
            amount = money.format_amount(abs(self.difference), self.summary.session.unit)
            suffix = "extra" if self.difference > 0 else "still to account for" if self.missing else "missing"
            return f"{amount} {suffix}."
        return "Total matches so far; finish counting."


def count_total(session_or_summary) -> CountTotal:
    found = session_or_summary if isinstance(session_or_summary, Summary) else summary(session_or_summary)
    return CountTotal(found)


def group_rake(group):
    """Accepted fees in native units, with a reconciling per-set breakdown."""
    from django.db.models import Sum
    rows = list(RakeEntry.objects.filter(account__group=group, buy_in__reversal__isnull=True)
                .filter(buy_in__session__night__archived_at__isnull=True)
                .values("unit", "buy_in__session_id", "buy_in__session__set_number",
                        "buy_in__session__night_id", "buy_in__session__game_date",
                        "buy_in__session__table__name")
                .annotate(total=Sum("amount")).order_by("-buy_in__session__game_date", "-buy_in__session_id"))
    totals = {"php": 0, "chips": 0}
    for row in rows:
        totals[row["unit"]] += row["total"]
    return totals, rows


def night_has_records(night) -> bool:
    """True when any ledger row exists under the session's sets, reversed and voided rows included."""
    from .models import CashOutBatch, Finalization
    return any(
        model.objects.filter(session__night=night).exists()
        for model in (BuyIn, FinalCount, CashOut, CashOutBatch, BalanceAdjustment, Finalization)
    )
