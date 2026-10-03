"""Finalization and settle-up. Depends on ledger for results; ledger does not depend on this app."""

from django.db import transaction

from audit import services as audit
from games import services as games
from games.models import GameSession
from groups.access import require_host
from groups.errors import RuleError
from groups.models import Member
from ledger import money
from ledger import services as ledger
from ledger.models import Finalization

from . import algorithm
from .models import Payment, PaymentReversal, SettlementPlan, Transfer

State = GameSession.State


@transaction.atomic
def finalize(session_id, actor: Member) -> Finalization:
    """Freeze the results and list who pays whom, in one transaction.

    Either every row is written and the session becomes finalized, or nothing
    changes. Finalizing says nothing about whether anyone has paid.
    """
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    if session.state == State.FINALIZED:
        return session.finalizations.get(is_current=True)  # a repeated tap
    if session.state != State.RECONCILIATION:
        raise RuleError("End play and record the cash-outs before finalizing.")
    finalization = ledger.write_results(session, actor)
    results = list(finalization.results.select_related("participant").order_by("participant__join_order"))
    # No payment is recorded before finalization yet, so each balance equals the result.
    owed = algorithm.balances({result.participant_id: result.net for result in results})
    parties = [(result.participant_id, owed[result.participant_id]) for result in results]
    transfers = algorithm.settle(parties)
    plan = SettlementPlan.objects.create(
        finalization=finalization, proven_minimal=algorithm.is_proven_minimal(parties)
    )
    Transfer.objects.bulk_create(
        Transfer(plan=plan, position=position, payer_id=payer, payee_id=payee, amount=amount)
        for position, (payer, payee, amount) in enumerate(transfers, start=1)
    )
    left = dict(parties)
    for payer, payee, amount in transfers:
        left[payer] += amount
        left[payee] -= amount
    if any(left.values()):
        raise ledger.LedgerInvariantError(f"Session {session.pk}: the transfers do not clear every balance.")
    audit.record(
        "session.finalized", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=finalization,
        summary=f"Finalized: {money.format_amount(finalization.total_buy_in, session.unit)} bought in, "
        f"{len(transfers)} transfer{'s' if len(transfers) != 1 else ''}",
        data={"nets": {str(r.participant_id): r.net for r in results}},
    )
    games.mark_finalized(session)
    return finalization


def _current_transfer(session, transfer_id) -> Transfer:
    transfer = (
        Transfer.objects.select_related("payer__member", "payee__member")
        .filter(pk=transfer_id, plan__finalization__session=session, plan__finalization__is_current=True)
        .first()
    )
    if transfer is None:
        raise RuleError("That transfer is not in this game's current results.")
    return transfer


def _describe(transfer, unit) -> str:
    return (
        f"{transfer.payer.member.display_name} → {transfer.payee.member.display_name} "
        f"{money.format_amount(transfer.amount, unit)}"
    )


@transaction.atomic
def mark_paid(session_id, actor: Member, transfer_id, request_id) -> Payment:
    """Record that a transfer was paid. Marking it twice changes nothing."""
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    if session.state != State.FINALIZED:
        raise RuleError("Transfers exist only after the results are final.")
    transfer = _current_transfer(session, transfer_id)
    existing = Payment.objects.filter(transfer=transfer, active=True).first()
    if existing is not None:
        return existing
    repeated = Payment.objects.filter(session=session, request_id=request_id).first()
    if repeated is not None:
        return repeated
    payment = Payment.objects.create(
        session=session, payer=transfer.payer, payee=transfer.payee, amount=transfer.amount,
        transfer=transfer, request_id=request_id, recorded_by=actor.user,
    )
    audit.record(
        "transfer.paid", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=transfer,
        summary=f"Marked paid: {_describe(transfer, session.unit)}",
    )
    games.touch(session)
    return payment


@transaction.atomic
def mark_unpaid(session_id, actor: Member, transfer_id, reason: str = "") -> None:
    """Undo a paid mark. The payment row stays, with a reversal."""
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    if session.state != State.FINALIZED:
        raise RuleError("Transfers exist only after the results are final.")
    transfer = _current_transfer(session, transfer_id)
    payment = Payment.objects.filter(transfer=transfer, active=True).first()
    if payment is None:
        return
    payment.active = False
    payment.save(update_fields=["active"])
    PaymentReversal.objects.create(payment=payment, reason=(reason or "").strip()[:255], recorded_by=actor.user)
    audit.record(
        "transfer.unpaid", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=transfer,
        summary=f"Marked unpaid again: {_describe(transfer, session.unit)}", reason=reason,
    )
    games.touch(session)
