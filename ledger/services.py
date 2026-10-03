"""The only code allowed to change money records.

Every function locks the session row first, so writes to one session run one
at a time. Records are append-only: a correction is a reversal with a reason.
"""

from django.db import transaction

from audit import services as audit
from games import services as games
from games.models import GameSession, Participant
from groups.access import require_host
from groups.errors import RuleError
from groups.models import Member

from . import money
from .models import BuyIn, BuyInReversal

State = GameSession.State
BUY_IN_STATES = (State.OPEN, State.RUNNING)
REVERSAL_STATES = (State.OPEN, State.RUNNING, State.RECONCILIATION)


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


def _accepted_buy_ins(session):
    return BuyIn.objects.filter(session=session, reversal__isnull=True)


@transaction.atomic
def record_buy_in(session_id, actor: Member, participant_id, amount_centavos: int, request_id) -> BuyIn:
    """Record a buy-in or rebuy. The first accepted buy-in locks the session's chip rate."""
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
    if not isinstance(amount_centavos, int) or isinstance(amount_centavos, bool):
        raise RuleError("Enter the buy-in amount.")
    current = games.current_settings(session)
    if not current.min_buy_in_centavos <= amount_centavos <= current.max_buy_in_centavos:
        raise RuleError(
            f"A buy-in must be between {money.format_pesos(current.min_buy_in_centavos)} "
            f"and {money.format_pesos(current.max_buy_in_centavos)}."
        )
    rate = session.rate or games.chip_rate(current)
    try:
        chips = money.chips_for_amount(amount_centavos, rate)
    except money.MoneyError as error:
        raise RuleError(str(error)) from None
    if session.rate is None:
        session.rate_centavos, session.rate_chips = rate
        session.save(update_fields=["rate_centavos", "rate_chips"])
    buy_in = BuyIn.objects.create(
        session=session, participant=participant, settings_version=current, amount_centavos=amount_centavos,
        chips=chips, request_id=request_id, recorded_by=actor.user,
    )
    audit.record(
        "buy_in.recorded", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=buy_in,
        summary=f"{participant.member.display_name} bought in for {money.format_pesos(amount_centavos)} ({chips:,} chips)",
        data={"amount_centavos": amount_centavos, "chips": chips},
    )
    games.touch(session)
    return buy_in


@transaction.atomic
def reverse_buy_in(session_id, actor: Member, buy_in_id, reason: str) -> BuyInReversal:
    """Void a buy-in. The row stays. When no accepted buy-in remains, the chip rate unlocks."""
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
    if not _accepted_buy_ins(session).exists():
        session.rate_centavos = session.rate_chips = None
        session.save(update_fields=["rate_centavos", "rate_chips"])
    audit.record(
        "buy_in.reversed", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=buy_in,
        summary=f"Reversed {buy_in.participant.member.display_name}'s buy-in of {money.format_pesos(buy_in.amount_centavos)}",
        reason=reversal.reason,
    )
    games.touch(session)
    return reversal


def guard_participant_exit(participant: Participant) -> None:
    """A player with money in the session cannot be withdrawn."""
    if BuyIn.objects.filter(participant=participant, reversal__isnull=True).exists():
        raise RuleError(
            f"{participant.member.display_name} has buy-ins in this game. Record a cash-out, or reverse the buy-ins first."
        )
