"""Finalizing a set, and settling a session. Depends on ledger for results; ledger does not depend on this app.

A set is finalized on its own: that freezes its results. Who pays whom is
decided once per session, over all of its sets, when the host closes it.
"""

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from audit import services as audit
from games import services as games
from games.models import GameNight, GameSession
from groups.access import require_host
from groups.errors import RuleError
from groups.models import Member
from ledger import money
from ledger import services as ledger
from ledger.models import Finalization, PlayerResult

from . import algorithm
from .models import Payment, PaymentReversal, SettlementPlan, Transfer

State = GameSession.State


@transaction.atomic
def finalize(session_id, actor: Member) -> Finalization:
    """Freeze the results of one set. It lists no transfers and says nothing about payment."""
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    if session.state == State.FINALIZED:
        return session.finalizations.get(is_current=True)  # a repeated tap
    if session.state != State.RECONCILIATION:
        raise RuleError("End play and record the cash-outs before finalizing.")
    finalization = ledger.write_results(session, actor)
    results = list(finalization.results.all())
    audit.record(
        "session.finalized", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=finalization,
        summary=f"Finalized set {session.set_number}: "
        f"{money.format_amount(finalization.total_buy_in, session.unit)} bought in",
        data={"nets": {str(r.participant_id): r.net for r in results}},
    )
    games.mark_finalized(session)
    return finalization


def session_results(night: GameNight) -> list:
    """Each member's result over the finalized sets of a session, in the order they first joined it.

    Returns ``[(member_id, net, sets_played)]``. Nets are after rake; add collected rake for settlement balances.
    """
    return [(member_id, net, played) for member_id, net, played, _ in session_standings(night)]


def result_rows(night: GameNight) -> list:
    """``[(member_id, net, play_seconds, rake_total)]`` of the current results, by set then join order."""
    return list(
        PlayerResult.objects.filter(is_current=True, finalization__session__night=night)
        .order_by("finalization__session__set_number", "participant__join_order")
        .values_list("member_id", "net", "play_seconds", "rake_total")
    )


def session_standings(night: GameNight, rows=None) -> list:
    """``[(member_id, net, sets_played, play_seconds)]`` over the finalized sets, in first-join order.

    ``play_seconds`` is None when none of the member's sets recorded playing time.
    ``rows`` is ``result_rows(night)`` when the caller has already read it.
    """
    totals, played, seconds = {}, {}, {}
    for member_id, net, play_seconds, _ in result_rows(night) if rows is None else rows:
        totals[member_id] = totals.get(member_id, 0) + net
        played[member_id] = played.get(member_id, 0) + 1
        if play_seconds is not None:
            seconds[member_id] = seconds.get(member_id, 0) + play_seconds
    return [(member_id, net, played[member_id], seconds.get(member_id)) for member_id, net in totals.items()]


def settlement_balances(night, rows=None):
    """Remaining player balances: add back the fee already collected at buy-in."""
    totals = {}
    for member_id, net, _, rake in result_rows(night) if rows is None else rows:
        totals[member_id] = totals.get(member_id, 0) + net + rake
    return list(totals.items())


@transaction.atomic
def close_night(night_id, actor: Member) -> SettlementPlan:
    """Close a session and list who pays whom, netted over all of its sets.

    Every set must be finalized or canceled. Closing says nothing about
    whether anyone has paid.
    """
    require_host(actor)
    night = games.lock_night(night_id, actor.group_id)
    if night.is_closed:
        plan = SettlementPlan.objects.filter(night=night).first()
        if plan is not None:
            return plan  # a repeated tap
        raise RuleError("This session is closed and has no results to settle.")
    sets = list(night.sets.order_by("set_number"))
    unfinished = [s for s in sets if s.state not in (State.FINALIZED, State.CANCELED)]
    if unfinished:
        names = ", ".join(f"set {s.set_number} ({s.get_state_display().lower()})" for s in unfinished)
        raise RuleError(f"Finalize or cancel every set first. Not done: {names}.")
    if not any(s.state == State.FINALIZED for s in sets):
        raise RuleError("No set of this session is finalized, so there is nothing to settle.")

    parties = settlement_balances(night)
    if sum(net for _, net in parties) != 0:
        raise ledger.LedgerInvariantError(f"Session {night.pk}: the results of its sets do not sum to zero.")
    transfers = algorithm.settle(parties)
    plan = SettlementPlan.objects.create(night=night, proven_minimal=algorithm.is_proven_minimal(parties))
    Transfer.objects.bulk_create(
        Transfer(plan=plan, position=position, payer_id=payer, payee_id=payee, amount=amount)
        for position, (payer, payee, amount) in enumerate(transfers, start=1)
    )
    left = dict(parties)
    for payer, payee, amount in transfers:
        left[payer] += amount
        left[payee] -= amount
    if any(left.values()):
        raise ledger.LedgerInvariantError(f"Session {night.pk}: the transfers do not clear every balance.")
    night.status = GameNight.Status.CLOSED
    night.closed_at = timezone.now()
    night.save(update_fields=["status", "closed_at"])
    audit.record(
        "night.closed", actor=actor.user, group_id=night.group_id, session_id=sets[-1].pk, target=night,
        summary=f"Closed the session: {len(sets)} set{'' if len(sets) == 1 else 's'}, "
        f"{len(transfers)} transfer{'' if len(transfers) == 1 else 's'}",
        data={"nets": {str(member_id): net for member_id, net in parties}},
    )
    # Open set pages poll their set's version: bump it so they show the closed session.
    GameSession.objects.filter(night=night).update(version=F("version") + 1)
    return plan


def _transfer(night, transfer_id) -> Transfer:
    transfer = Transfer.objects.select_related("payer", "payee").filter(pk=transfer_id, plan__night=night).first()
    if transfer is None:
        raise RuleError("That transfer is not in this session.")
    return transfer


def _describe(transfer, unit) -> str:
    return f"{transfer.payer.display_name} → {transfer.payee.display_name} {money.format_amount(transfer.amount, unit)}"


def _latest_set_id(night):
    return night.sets.order_by("-set_number").values_list("pk", flat=True).first()


@transaction.atomic
def mark_paid(night_id, actor: Member, transfer_id, request_id) -> Payment:
    """Record that a transfer was paid. Marking it twice changes nothing."""
    require_host(actor)
    night = games.lock_night(night_id, actor.group_id)
    if not night.is_closed:
        raise RuleError("Transfers exist only after the session is closed.")
    transfer = _transfer(night, transfer_id)
    existing = Payment.objects.filter(transfer=transfer, active=True).first()
    if existing is not None:
        return existing
    repeated = Payment.objects.filter(night=night, request_id=request_id).first()
    if repeated is not None:
        return repeated
    payment = Payment.objects.create(
        night=night, payer=transfer.payer, payee=transfer.payee, amount=transfer.amount, transfer=transfer,
        request_id=request_id, recorded_by=actor.user,
    )
    audit.record(
        "transfer.paid", actor=actor.user, group_id=night.group_id, session_id=_latest_set_id(night), target=transfer,
        summary=f"Marked paid: {_describe(transfer, night.unit)}",
    )
    return payment


@transaction.atomic
def mark_unpaid(night_id, actor: Member, transfer_id, reason: str = "") -> None:
    """Undo a paid mark. The payment row stays, with a reversal."""
    require_host(actor)
    night = games.lock_night(night_id, actor.group_id)
    if not night.is_closed:
        raise RuleError("Transfers exist only after the session is closed.")
    transfer = _transfer(night, transfer_id)
    payment = Payment.objects.filter(transfer=transfer, active=True).first()
    if payment is None:
        return
    payment.active = False
    payment.save(update_fields=["active"])
    PaymentReversal.objects.create(payment=payment, reason=(reason or "").strip()[:255], recorded_by=actor.user)
    audit.record(
        "transfer.unpaid", actor=actor.user, group_id=night.group_id, session_id=_latest_set_id(night), target=transfer,
        summary=f"Marked unpaid again: {_describe(transfer, night.unit)}", reason=reason,
    )
