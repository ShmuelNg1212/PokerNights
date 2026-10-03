"""The only code allowed to change money records.

Every function locks the session row first, so writes to one session run one
at a time. Records are append-only: a correction is a reversal with a reason.
Each amount is an integer in the session's unit (pesos or chips).
"""

from django.db import transaction
from django.utils import timezone

from audit import services as audit
from games import services as games
from games.models import GameSession, Participant
from groups.access import require_host
from groups.errors import RuleError
from groups.models import Member

from . import money, queries
from .models import (
    BalanceAdjustment, BuyIn, BuyInReversal, CashOut, CashOutReversal, Finalization, PlayerResult,
)

State = GameSession.State
BUY_IN_STATES = (State.OPEN, State.RUNNING)
REVERSAL_STATES = (State.OPEN, State.RUNNING, State.RECONCILIATION)
CASH_OUT_STATES = (State.RUNNING, State.RECONCILIATION)


def _participant(session, participant_id) -> Participant:
    participant = Participant.objects.select_related("member").filter(session=session, pk=participant_id).first()
    if participant is None:
        raise RuleError("That player is not in this game.")
    return participant


def _clean_reason(reason) -> str:
    reason = " ".join((reason or "").split())[:255]
    if not reason:
        raise RuleError("Give a reason. It stays in the game log.")
    return reason


def _is_amount(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _accepted_buy_ins(session):
    return BuyIn.objects.filter(session=session, reversal__isnull=True)


@transaction.atomic
def record_buy_in(session_id, actor: Member, participant_id, amount: int, request_id) -> BuyIn:
    """Record a buy-in or rebuy, in the session's unit."""
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    repeated = BuyIn.objects.filter(session=session, request_id=request_id).first()
    if repeated is not None:
        return repeated
    if session.state not in BUY_IN_STATES:
        raise RuleError("Buy-ins can be recorded only while the game is open or running.")
    participant = _participant(session, participant_id)
    if participant.status != Participant.Status.JOINED:
        raise RuleError(f"{participant.member.display_name} is not at the table.")
    if not _is_amount(amount):
        raise RuleError("Enter the buy-in amount.")
    current = games.current_settings(session)
    if not current.min_buy_in <= amount <= current.max_buy_in:
        raise RuleError(
            f"A buy-in must be between {money.format_amount(current.min_buy_in, session.unit)} "
            f"and {money.format_amount(current.max_buy_in, session.unit)}."
        )
    buy_in = BuyIn.objects.create(
        session=session, participant=participant, settings_version=current, amount=amount,
        request_id=request_id, recorded_by=actor.user,
    )
    audit.record(
        "buy_in.recorded", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=buy_in,
        summary=f"{participant.member.display_name} bought in for {money.format_amount(amount, session.unit)}",
        data={"amount": amount, "unit": session.unit},
    )
    games.touch(session)
    return buy_in


@transaction.atomic
def reverse_buy_in(session_id, actor: Member, buy_in_id, reason: str) -> BuyInReversal:
    """Void a buy-in. The row stays in the log."""
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    buy_in = BuyIn.objects.select_related("participant__member").filter(session=session, pk=buy_in_id).first()
    if buy_in is None:
        raise RuleError("That buy-in is not in this game.")
    existing = BuyInReversal.objects.filter(buy_in=buy_in).first()
    if existing is not None:
        return existing
    if session.state not in REVERSAL_STATES:
        raise RuleError("This game is closed. Its records cannot change.")
    reversal = BuyInReversal.objects.create(buy_in=buy_in, reason=_clean_reason(reason), recorded_by=actor.user)
    audit.record(
        "buy_in.reversed", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=buy_in,
        summary=f"Reversed {buy_in.participant.member.display_name}'s buy-in of {money.format_amount(buy_in.amount, session.unit)}",
        reason=reversal.reason,
    )
    games.touch(session)
    return reversal


@transaction.atomic
def record_cash_out(session_id, actor: Member, participant_id, amount: int, request_id, *, left=False) -> CashOut:
    """Record what a player takes off the table. ``left`` also marks the player as gone for the night."""
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    repeated = CashOut.objects.filter(session=session, request_id=request_id).first()
    if repeated is not None:
        return repeated
    if session.state not in CASH_OUT_STATES:
        raise RuleError("Cash-outs can be recorded only during the game or while counting up.")
    participant = _participant(session, participant_id)
    if not _is_amount(amount) or amount < 0:
        raise RuleError("Enter the cash-out amount, 0 or more.")
    if not _accepted_buy_ins(session).filter(participant=participant).exists():
        raise RuleError(f"{participant.member.display_name} has no buy-in, so there is nothing to cash out.")
    cash_out = CashOut.objects.create(
        session=session, participant=participant, amount=amount, request_id=request_id, recorded_by=actor.user
    )
    audit.record(
        "cash_out.recorded", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=cash_out,
        summary=f"{participant.member.display_name} cashed out {money.format_amount(amount, session.unit)}",
        data={"amount": amount, "unit": session.unit},
    )
    games.touch(session)
    if left and participant.status == Participant.Status.JOINED:
        games.set_left(session.pk, actor, participant.pk)
    return cash_out


@transaction.atomic
def reverse_cash_out(session_id, actor: Member, cash_out_id, reason: str) -> CashOutReversal:
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    cash_out = CashOut.objects.select_related("participant__member").filter(session=session, pk=cash_out_id).first()
    if cash_out is None:
        raise RuleError("That cash-out is not in this game.")
    existing = CashOutReversal.objects.filter(cash_out=cash_out).first()
    if existing is not None:
        return existing
    if session.state not in CASH_OUT_STATES:
        raise RuleError("This game is closed. Its records cannot change.")
    reversal = CashOutReversal.objects.create(cash_out=cash_out, reason=_clean_reason(reason), recorded_by=actor.user)
    audit.record(
        "cash_out.reversed", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=cash_out,
        summary=f"Reversed {cash_out.participant.member.display_name}'s cash-out of {money.format_amount(cash_out.amount, session.unit)}",
        reason=reversal.reason,
    )
    games.touch(session)
    return reversal


@transaction.atomic
def record_override(session_id, actor: Member, note: str, mode: str, participant_id, request_id) -> list:
    """Let unbalanced books be finalized: the host states, with a note, who absorbs the difference.

    ``mode`` is ``player`` (one named player takes all of it) or ``equal``
    (every player with a buy-in takes an equal share; units that do not divide
    go one each to players in join order). Nothing is adjusted without this call.
    """
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    repeated = list(BalanceAdjustment.objects.filter(session=session, request_id=request_id))
    if repeated:
        return repeated
    if session.state != State.RECONCILIATION:
        raise RuleError("An override can be recorded only while counting up.")
    found = queries.balance(session)
    if not found.counted:
        raise RuleError(found.explanation)
    if found.difference == 0:
        raise RuleError("The books balance. No override is needed.")
    note = " ".join((note or "").split())[:255]
    if not note:
        raise RuleError("Write a note that explains the override. It stays in the game log.")
    players = found.summary.money_lines
    if mode == BalanceAdjustment.Mode.PLAYER:
        line = next((line for line in players if str(line.participant.pk) == str(participant_id)), None)
        if line is None:
            raise RuleError("Select a player of this game who has a buy-in.")
        shares = [(line.participant, -found.difference)]
    elif mode == BalanceAdjustment.Mode.EQUAL:
        parts = money.split_equal(-found.difference, len(players))
        shares = [(line.participant, part) for line, part in zip(players, parts) if part]
    else:
        raise RuleError("Select who absorbs the difference.")
    rows = [
        BalanceAdjustment.objects.create(
            session=session, participant=participant, amount=share, mode=mode, note=note,
            request_id=request_id, recorded_by=actor.user,
        )
        for participant, share in shares
    ]
    audit.record(
        "balance.overridden", actor=actor.user, group_id=session.group_id, session_id=session.pk,
        summary=f"Override: {found.difference_text} {found.direction} absorbed "
        + ("equally by all players" if mode == BalanceAdjustment.Mode.EQUAL else f"by {shares[0][0].member.display_name}"),
        reason=note, data={"difference": found.difference, "shares": {str(p.pk): d for p, d in shares}},
    )
    games.touch(session)
    return rows


@transaction.atomic
def void_override(session_id, actor: Member) -> int:
    """Remove the active override, for example after a cash-out was corrected. The rows stay, marked void."""
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    if session.state != State.RECONCILIATION:
        raise RuleError("An override can be removed only while counting up.")
    count = BalanceAdjustment.objects.filter(session=session, voided_at__isnull=True).update(
        voided_at=timezone.now(), voided_by=actor.user
    )
    if count:
        audit.record(
            "balance.override_removed", actor=actor.user, group_id=session.group_id, session_id=session.pk,
            summary="Removed the balance override",
        )
        games.touch(session)
    return count


class LedgerInvariantError(Exception):
    """The books failed a conservation check. The transaction must roll back; this is a defect, not user error."""


def write_results(session: GameSession, actor: Member) -> Finalization:
    """Freeze each player's result. Call inside a transaction, with the session locked.

    Refuses unless the balance check passes. A result is cash-outs plus any
    override, minus buy-ins. Results always sum to zero.
    """
    found = queries.balance(session)
    if not found.ok:
        raise RuleError(found.explanation)
    lines = found.summary.money_lines
    total_buy_in = found.summary.total
    total_cash_out = sum(line.cash_out_final for line in lines)
    nets = [line.cash_out_final - line.buy_in_total for line in lines]
    if total_cash_out != total_buy_in or sum(nets) != 0:
        raise LedgerInvariantError(
            f"Session {session.pk}: cash-outs {total_cash_out} do not equal buy-ins {total_buy_in}."
        )
    previous = session.finalizations.order_by("-revision").first()
    if previous is not None:
        Finalization.objects.filter(session=session, is_current=True).update(is_current=False)
        PlayerResult.objects.filter(finalization__session=session, is_current=True).update(is_current=False)
    finalization = Finalization.objects.create(
        session=session,
        revision=previous.revision + 1 if previous else 1,
        unit=session.unit,
        total_buy_in=total_buy_in,
        total_cash_out=total_cash_out,
        raw_difference=found.raw_difference,
        settings_snapshot=[
            {"number": version.number, **version.stakes()} for version in session.settings_versions.order_by("number")
        ],
        finalized_by=actor.user,
    )
    PlayerResult.objects.bulk_create(
        PlayerResult(
            finalization=finalization,
            participant=line.participant,
            member_id=line.participant.member_id,
            group_id=session.group_id,
            game_date=session.game_date,
            unit=session.unit,
            buy_in_total=line.buy_in_total,
            buy_in_count=line.buy_in_count,
            cashed_out=line.cashed_out,
            adjustment=line.adjustment,
            cash_out=line.cash_out_final,
            net=net,
        )
        for line, net in zip(lines, nets)
    )
    return finalization


def session_has_money(session: GameSession) -> bool:
    return (
        BuyIn.objects.filter(session=session, reversal__isnull=True).exists()
        or CashOut.objects.filter(session=session, reversal__isnull=True).exists()
    )


def guard_participant_exit(participant: Participant) -> None:
    """A player with money in the session cannot be withdrawn."""
    has_cash_out = CashOut.objects.filter(participant=participant, reversal__isnull=True).exists()
    if has_cash_out or BuyIn.objects.filter(participant=participant, reversal__isnull=True).exists():
        raise RuleError(
            f"{participant.member.display_name} has buy-ins in this game. Record a cash-out, or reverse the buy-ins first."
        )
