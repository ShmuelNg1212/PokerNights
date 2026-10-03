"""The only code allowed to change money records.

Every function locks the session row first, so writes to one session run one
at a time. Records are append-only: a correction is a reversal with a reason.
Each amount is an integer in the session's unit (pesos or chips).
"""

import uuid

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
    BalanceAdjustment, BuyIn, BuyInReversal, CashOut, CashOutBatch, CashOutReversal, FinalCount, Finalization,
    PlayerResult,
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


def _final_cash_outs(participant):
    return CashOut.objects.filter(participant=participant, kind=CashOut.Kind.FINAL, reversal__isnull=True)


def _void_count(participant, user) -> None:
    FinalCount.objects.filter(participant=participant, is_current=True).update(
        is_current=False, voided_at=timezone.now(), voided_by=user
    )


def _back_in_play(participant, actor: Member) -> None:
    """The player plays on after a final cash-out: that cash-out was partial after all."""
    changed = _final_cash_outs(participant).update(kind=CashOut.Kind.PARTIAL)
    if changed:
        audit.record(
            "cash_out.reclassified", actor=actor.user, group_id=participant.session.group_id,
            session_id=participant.session_id, target=participant,
            summary=f"{participant.member.display_name} plays on; the earlier cash-out now counts as partial",
        )


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
    _back_in_play(participant, actor)
    if session.state == State.RUNNING:
        games.clock.open_interval(participant, timezone.now())
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
    if _final_cash_outs(participant).exists():
        raise RuleError(
            f"{participant.member.display_name} is already cashed out. Reverse that cash-out to change it."
        )
    # A cash-out is the player's last when they leave, or when play has ended.
    final = left or session.state == State.RECONCILIATION
    cash_out = CashOut.objects.create(
        session=session, participant=participant, amount=amount, request_id=request_id, recorded_by=actor.user,
        kind=CashOut.Kind.FINAL if final else CashOut.Kind.PARTIAL,
    )
    if final:
        _void_count(participant, actor.user)  # an unused count would contradict this cash-out
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
    if cash_out.final_count_id:
        # The count behind this cash-out is void too: the player is "awaiting count" again.
        FinalCount.objects.filter(pk=cash_out.final_count_id).update(
            is_current=False, voided_at=timezone.now(), voided_by=actor.user
        )
    audit.record(
        "cash_out.reversed", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=cash_out,
        summary=f"Reversed {cash_out.participant.member.display_name}'s cash-out of {money.format_amount(cash_out.amount, session.unit)}",
        reason=reversal.reason,
    )
    games.touch(session)
    return reversal


def _check_countable(session, participant, amount) -> None:
    """The rules a final count must pass. Raises RuleError naming the player."""
    name = participant.member.display_name
    if not _is_amount(amount) or amount < 0:
        raise RuleError(f"Enter {name}'s final count, 0 or more.")
    if not _accepted_buy_ins(session).filter(participant=participant).exists():
        raise RuleError(f"{name} has no buy-in, so there is nothing to count.")
    if _final_cash_outs(participant).exists():
        raise RuleError(f"{name} is already cashed out. Reverse that cash-out to count again.")


def _write_count(session, actor, participant, amount, request_id) -> FinalCount:
    """Store a confirmed count as the player's current one, with the next version."""
    latest = FinalCount.objects.filter(participant=participant).order_by("-version").first()
    FinalCount.objects.filter(participant=participant, is_current=True).update(is_current=False)
    count = FinalCount.objects.create(
        session=session, participant=participant, amount=amount, version=(latest.version + 1) if latest else 1,
        request_id=request_id, confirmed_by=actor.user,
    )
    audit.record(
        "count.confirmed", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=count,
        summary=f"Confirmed {participant.member.display_name}'s final count: "
        f"{money.format_amount(amount, session.unit)}" + (f" (version {count.version})" if count.version > 1 else ""),
        data={"amount": amount, "version": count.version},
    )
    return count


@transaction.atomic
def confirm_count(session_id, actor: Member, participant_id, amount: int, request_id) -> FinalCount:
    """Confirm what a player has at the end of the set. Zero is a valid count; a missing one is not zero.

    Confirming again replaces the count with the next version. This records no cash-out.
    """
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    repeated = FinalCount.objects.filter(session=session, request_id=request_id).first()
    if repeated is not None:
        return repeated
    if session.state != State.RECONCILIATION:
        raise RuleError("Final counts are confirmed after play has ended.")
    participant = _participant(session, participant_id)
    _check_countable(session, participant, amount)
    count = _write_count(session, actor, participant, amount, request_id)
    games.touch(session)
    return count


@transaction.atomic
def confirm_counts(session_id, actor: Member, amounts: dict, request_id) -> list:
    """Confirm several players' final counts in one action: all of them, or none.

    ``amounts`` maps a participant id to an integer amount. Only the players in
    it are touched; anyone left out stays as they are and is never read as
    zero. A player whose current count already equals the amount is skipped, so
    no needless version is written. Returns the counts that were written.
    """
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    if not amounts:
        raise RuleError("Type at least one final count. Type 0 for a player who has nothing left.")
    # One submission writes several rows; each gets its own id derived from the form's.
    ids = {participant_id: uuid.uuid5(request_id, str(participant_id)) for participant_id in amounts}
    if FinalCount.objects.filter(session=session, request_id__in=ids.values()).exists():
        return list(FinalCount.objects.filter(session=session, request_id__in=ids.values()))  # a repeated submission
    if session.state != State.RECONCILIATION:
        raise RuleError("Final counts are confirmed after play has ended.")
    checked = []
    for participant_id, amount in amounts.items():
        participant = _participant(session, participant_id)
        _check_countable(session, participant, amount)
        current = FinalCount.objects.filter(participant=participant, is_current=True).first()
        if current is None or current.amount != amount:
            checked.append((participant, amount, ids[participant_id]))
    # Every value passed. Only now is anything written.
    written = [_write_count(session, actor, participant, amount, rid) for participant, amount, rid in checked]
    if written:
        games.touch(session)
    return written


@transaction.atomic
def clear_count(session_id, actor: Member, participant_id) -> None:
    """Take back a confirmed count that is not cashed out yet. The player is "awaiting count" again."""
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    if session.state != State.RECONCILIATION:
        raise RuleError("Final counts can change only after play has ended.")
    participant = _participant(session, participant_id)
    if FinalCount.objects.filter(participant=participant, is_current=True).exists():
        _void_count(participant, actor.user)
        audit.record(
            "count.cleared", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=participant,
            summary=f"Cleared {participant.member.display_name}'s final count",
        )
        games.touch(session)


@transaction.atomic
def cash_out_counted(session_id, actor: Member, count_ids, request_id) -> CashOutBatch:
    """Cash out, in one action, the players whose confirmed counts the host just reviewed.

    ``count_ids`` are the exact counts shown in the review. Each must still be
    the player's current count, and the player must not be cashed out. If any
    check fails, nothing is recorded. This does not finalize the set and marks
    no payment.
    """
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    repeated = CashOutBatch.objects.filter(session=session, request_id=request_id).first()
    if repeated is not None:
        return repeated
    if session.state != State.RECONCILIATION:
        raise RuleError("Counted players are cashed out after play has ended.")
    wanted = []
    for count_id in count_ids:
        try:
            count_id = int(count_id)
        except (TypeError, ValueError):
            raise RuleError("That review is not valid. Open the review again.") from None
        if count_id not in wanted:
            wanted.append(count_id)
    if not wanted:
        raise RuleError("No player has a confirmed count yet.")

    counts = FinalCount.objects.select_related("participant__member").filter(session=session, pk__in=wanted).in_bulk()
    if len(counts) != len(wanted):
        raise RuleError("That review does not belong to this set. Nothing was recorded. Open the review again.")
    stale = []
    for count_id in wanted:
        count = counts[count_id]
        name = count.participant.member.display_name
        if _final_cash_outs(count.participant).exists():
            stale.append(f"{name} was cashed out in the meantime")
        elif not count.is_current:
            stale.append(f"{name}'s count was changed or cleared")
    if stale:
        raise RuleError(
            f"The review is out of date: {'; '.join(stale)}. Nothing was recorded. Check the new review and confirm again."
        )

    batch = CashOutBatch.objects.create(session=session, request_id=request_id, recorded_by=actor.user)
    ordered = sorted((counts[count_id] for count_id in wanted), key=lambda count: count.participant.join_order)
    for count in ordered:
        cash_out = CashOut.objects.create(
            session=session, participant=count.participant, amount=count.amount, kind=CashOut.Kind.FINAL,
            final_count=count, batch=batch, request_id=uuid.uuid4(), recorded_by=actor.user,
        )
        audit.record(
            "cash_out.recorded", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=cash_out,
            summary=f"{count.participant.member.display_name} cashed out "
            f"{money.format_amount(count.amount, session.unit)} (counted, batch)",
            data={"amount": count.amount, "unit": session.unit, "count_id": count.pk, "count_version": count.version},
        )
    total = sum(count.amount for count in ordered)
    audit.record(
        "cash_out.batch", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=batch,
        summary=f"Cashed out {len(ordered)} counted player{'' if len(ordered) == 1 else 's'}: "
        f"{', '.join(count.participant.member.display_name for count in ordered)} "
        f"({money.format_amount(total, session.unit)} in all)",
        data={"participants": [count.participant_id for count in ordered], "total": total},
    )
    games.touch(session)
    return batch


def void_counts_on_resume(session: GameSession, actor: Member) -> None:
    """Play resumes, so stacks will change: confirmed counts that are not cashed out are void."""
    count = FinalCount.objects.filter(session=session, is_current=True).update(
        is_current=False, voided_at=timezone.now(), voided_by=actor.user
    )
    if count:
        audit.record(
            "count.voided_on_resume", actor=actor.user, group_id=session.group_id, session_id=session.pk,
            summary=f"Play resumed: {count} confirmed count{'' if count == 1 else 's'} voided",
        )


def is_cashed_out(participant: Participant) -> bool:
    return _final_cash_outs(participant).exists()


def back_in_play(participant: Participant, actor: Member) -> None:
    _back_in_play(participant, actor)


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
    # Play ended before counting began, so every interval is closed: this is not "time until now".
    played = games.clock.player_seconds(session) if session.play_periods.exists() else {}
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
            play_seconds=played.get(line.participant.pk, 0) if played or session.play_periods.exists() else None,
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
