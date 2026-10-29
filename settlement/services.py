"""Finalizing a set, and settling a session. Depends on ledger for results; ledger does not depend on this app.

A set is finalized on its own: that freezes its results. Who pays whom is
decided once per session, over all of its sets, when the host closes it.
"""

from django.conf import settings
from django.db import transaction
from django.db.models import Exists, F, OuterRef
from django.utils import timezone

from audit import services as audit
from games import services as games
from games.models import GameNight, GameSession
from groups.access import require_host
from groups.errors import RuleError
from groups.models import GroupRakeAccount, Member
from ledger import money
from ledger import services as ledger
from ledger.models import Finalization, PlayerResult

from . import algorithm
from .models import CarriedTransfer, Payment, PaymentReversal, SettlementPlan, Transfer

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


def _reopen_reason(reason) -> str:
    if not settings.REOPENING:
        raise RuleError("Reopening is turned off.")
    reason = " ".join((reason or "").split())[:255]
    if not reason:
        raise RuleError("Give a reason for reopening. It stays in the log.")
    return reason


@transaction.atomic
def reopen_set(session_id, actor: Member, reason: str = "") -> GameSession:
    """Return a finalized set to counting up so the host can correct it. Finalizing again writes the next revision.

    The results leave the session's totals until then. The retired revision stays, with the reason.
    """
    require_host(actor)
    session = games.lock_session(session_id, actor.group_id)
    if ledger.is_reopened(session):
        return session  # a repeated tap
    if session.state != State.FINALIZED:
        raise RuleError("Only a finalized set can be reopened.")
    if session.night.is_closed:
        raise RuleError("The session is closed. Reopen the session first.")
    reason = _reopen_reason(reason)
    retired = ledger.void_results(session, actor, reason)
    audit.record(
        "session.reopened", actor=actor.user, group_id=session.group_id, session_id=session.pk, target=retired,
        summary=f"Reopened set {session.set_number} to correct it; results revision {retired.revision} replaced",
        reason=reason, data={"nets": {str(r.participant_id): r.net for r in retired.results.all()}},
    )
    games.mark_reopened(session)
    return session


@transaction.atomic
def reopen_night(night_id, actor: Member, reason: str = "") -> GameNight:
    """Open a closed session again: its who-pays-whom list is retired and closing writes a new one.

    Refused while a transfer is marked paid, so no list ever has to account for money that already moved.
    """
    require_host(actor)
    night = games.lock_night(night_id, actor.group_id)
    if not night.is_closed:
        return night  # a repeated tap
    reason = _reopen_reason(reason)
    plan = SettlementPlan.objects.filter(night=night, is_current=True).first()
    paid = Payment.objects.filter(transfer__plan=plan, active=True).count() if plan is not None else 0
    if paid:
        raise RuleError(
            f"{paid} transfer{' is' if paid == 1 else 's are'} marked paid. "
            f"Mark {'it' if paid == 1 else 'them'} unpaid first."
        )
    taken = _carried_by(plan) if plan is not None else None
    if taken is not None:
        raise RuleError(
            f"A transfer of this session was carried into the session of {_night_day(taken.plan.night)}. "
            "Reopen that session first."
        )
    released = CarriedTransfer.objects.filter(plan=plan).count() if plan is not None else 0
    if plan is not None:
        plan.is_current = False
        plan.voided_at, plan.voided_by, plan.void_reason = timezone.now(), actor.user, reason
        plan.save(update_fields=["is_current", "voided_at", "voided_by", "void_reason"])
    night.status = GameNight.Status.OPEN
    night.closed_at = None
    night.save(update_fields=["status", "closed_at"])
    audit.record(
        "night.reopened", actor=actor.user, group_id=night.group_id, session_id=_latest_set_id(night), target=night,
        summary="Reopened the session; its transfer list is replaced when it is closed again"
        + (f". {released} earlier transfer{' is' if released == 1 else 's are'} unpaid again" if released else ""),
        reason=reason,
    )
    # Open set pages poll their set's version: bump it so they show the open session.
    GameSession.objects.filter(night=night).update(version=F("version") + 1)
    return night


def session_results(night: GameNight) -> list:
    """Each member's result over the finalized sets of a session, in the order they first joined it.

    Returns ``[(member_id, net, sets_played)]``. Nets are after rake; add collected rake for settlement balances.
    """
    return [(member_id, net, played) for member_id, net, played, _ in session_standings(night)]


def result_rows(night: GameNight) -> list:
    """The current results of a session's finalized sets, by set then join order, in one query.

    Named rows: ``member_id``, ``net``, ``play_seconds``, ``rake_total``, ``session_id``,
    ``set_number``, ``buy_in_total``, ``buy_in_count`` and ``cash_out``.
    """
    return list(
        PlayerResult.objects.filter(is_current=True, finalization__session__night=night)
        .annotate(session_id=F("finalization__session_id"), set_number=F("finalization__session__set_number"))
        .order_by("set_number", "participant__join_order")
        .values_list(
            "member_id", "net", "play_seconds", "rake_total", "session_id", "set_number",
            "buy_in_total", "buy_in_count", "cash_out", named=True,
        )
    )


def session_standings(night: GameNight, rows=None) -> list:
    """``[(member_id, net, sets_played, play_seconds)]`` over the finalized sets, in first-join order.

    ``play_seconds`` is None when none of the member's sets recorded playing time.
    ``rows`` is ``result_rows(night)`` when the caller has already read it.
    """
    totals, played, seconds = {}, {}, {}
    for row in result_rows(night) if rows is None else rows:
        totals[row.member_id] = totals.get(row.member_id, 0) + row.net
        played[row.member_id] = played.get(row.member_id, 0) + 1
        if row.play_seconds is not None:
            seconds[row.member_id] = seconds.get(row.member_id, 0) + row.play_seconds
    return [(member_id, net, played[member_id], seconds.get(member_id)) for member_id, net in totals.items()]


# The rake fund's key among the parties of a settle-up. No member has this key.
RAKE_FUND = 0


def rake_to_fund(night) -> bool:
    """Whether the group settles collected rake into its rake fund (the group's current choice)."""
    choice = GroupRakeAccount.objects.filter(group_id=night.group_id).values_list("settlement", flat=True).first()
    return choice == GroupRakeAccount.Settlement.FUND


def settlement_balances(night, rows=None, *, to_fund=False):
    """Remaining balances. By default each player gets back the fee already collected at buy-in.

    With ``to_fund`` each player settles their result as it stands, and the rake fund (key
    ``RAKE_FUND``, last) receives the session's collected rake.
    """
    totals, rake = {}, 0
    for row in result_rows(night) if rows is None else rows:
        totals[row.member_id] = totals.get(row.member_id, 0) + row.net + (0 if to_fund else row.rake_total)
        rake += row.rake_total
    parties = list(totals.items())
    if to_fund and rake:
        parties.append((RAKE_FUND, rake))
    return parties


def _night_day(night) -> str:
    return f"{night.game_date:%b} {night.game_date.day}"


def _carried_by(plan):
    """The carry, in force, that took one of this list's transfers into a later session; None when none did."""
    return (
        CarriedTransfer.objects.filter(transfer__plan=plan, plan__is_current=True)
        .select_related("plan__night").order_by("pk").first()
    )


def _transfers_to_carry(night, parties, carry_ids) -> list:
    """The earlier transfers named by ``carry_ids``, each checked again with its session locked."""
    wanted = []
    for value in carry_ids or ():
        try:
            wanted.append(int(value))
        except (TypeError, ValueError):
            raise RuleError("Choose the earlier transfers from the list.") from None
    wanted = list(dict.fromkeys(wanted))
    if not wanted or not settings.CARRY_DEBTS:
        return []
    # The earlier sessions are locked in a fixed order, so a paid mark or a reopening there waits for this close.
    earlier = Transfer.objects.filter(pk__in=wanted).values_list("plan__night_id", flat=True)
    list(GameNight.objects.select_for_update().filter(pk__in=set(earlier)).order_by("pk").values_list("pk", flat=True))
    from . import queries

    allowed = {transfer.pk: transfer for transfer in queries.carryable(night, {member_id for member_id, _ in parties})}
    gone = [pk for pk in wanted if pk not in allowed]
    if gone:
        raise RuleError(
            f"{len(gone)} earlier transfer{' has' if len(gone) == 1 else 's have'} changed since this page was shown: "
            "paid, carried elsewhere, or no longer between two of tonight's players. Nothing was closed. Look at the list again."
        )
    return [allowed[pk] for pk in wanted]


def _carried(transfer):
    return CarriedTransfer.objects.filter(transfer=transfer, plan__is_current=True).select_related("plan__night").first()


@transaction.atomic
def close_night(night_id, actor: Member, carry_ids=()) -> SettlementPlan:
    """Close a session and list who pays whom, netted over all of its sets.

    Every set must be finalized or canceled. Closing says nothing about
    whether anyone has paid.

    Payments made at the table while the session was open are subtracted first (ADR 0002).

    ``carry_ids`` are unpaid transfers of earlier sessions to fold into this list: each one moves
    its amount from the payer's balance to the payee's before the netting, and is then carried,
    neither paid nor unpaid. Every one is checked again here; if one no longer qualifies nothing
    is closed.
    """
    require_host(actor)
    night = games.lock_night(night_id, actor.group_id)
    if night.is_closed:
        plan = SettlementPlan.objects.filter(night=night, is_current=True).first()
        if plan is not None:
            return plan  # a repeated tap
        raise RuleError("This session is closed and has no results to settle.")
    sets = list(night.sets.order_by("set_number"))
    unfinished = [s for s in sets if s.state not in (State.FINALIZED, State.CANCELED)]
    if unfinished:
        names = ", ".join(f"set {s.set_number} ({s.state_word.lower()})" for s in unfinished)
        raise RuleError(f"Finalize or cancel every set first. Not done: {names}.")
    if not any(s.state == State.FINALIZED for s in sets):
        raise RuleError("No set of this session is finalized, so there is nothing to settle.")

    to_fund = rake_to_fund(night)
    parties = settlement_balances(night, to_fund=to_fund)
    if sum(net for _, net in parties) != 0:
        raise ledger.LedgerInvariantError(f"Session {night.pk}: the results of its sets do not sum to zero.")
    carried = _transfers_to_carry(night, parties, carry_ids)
    if carried:
        balances = dict(parties)
        for old in carried:
            balances[old.payer_id] -= old.amount
            balances[old.payee_id] += old.amount
        parties = list(balances.items())
        if sum(net for _, net in parties) != 0:
            raise ledger.LedgerInvariantError(f"Session {night.pk}: the balances with carried transfers do not sum to zero.")
    at_table = list(
        Payment.objects.filter(night=night, transfer__isnull=True, active=True).values_list("payer_id", "payee_id", "amount")
    )
    # A buy-in reversed after a payment can leave it naming someone with no result: refuse, nothing is closed.
    stray = {member_id for payer, payee, _ in at_table for member_id in (payer, payee)} - {member_id for member_id, _ in parties}
    if stray:
        names = ", ".join(sorted(Member.objects.filter(pk__in=stray).values_list("display_name", flat=True)))
        raise RuleError(f"A payment at the table names {names}, who has no result in this session. Undo it first.")
    if at_table:
        parties = list(algorithm.balances(dict(parties), at_table).items())
        if sum(net for _, net in parties) != 0:
            raise ledger.LedgerInvariantError(f"Session {night.pk}: the balances with table payments do not sum to zero.")
    transfers = algorithm.settle(parties)
    plan = SettlementPlan.objects.create(
        night=night, proven_minimal=algorithm.is_proven_minimal(parties), rake_to_fund=to_fund
    )
    CarriedTransfer.objects.bulk_create(CarriedTransfer(transfer=old, plan=plan, created_by=actor.user) for old in carried)
    Transfer.objects.bulk_create(
        Transfer(
            plan=plan, position=position, payer_id=payer, amount=amount,
            payee_id=None if payee == RAKE_FUND else payee, to_rake_fund=payee == RAKE_FUND,
        )
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
        f"{len(transfers)} transfer{'' if len(transfers) == 1 else 's'}"
        + (f", {len(carried)} earlier transfer{'' if len(carried) == 1 else 's'} carried in" if carried else ""),
        data={
            "nets": {str(member_id): net for member_id, net in parties}, "carried": [old.pk for old in carried],
            "at_table": len(at_table),
        },
    )
    for old in carried:
        audit.record(
            "transfer.carried", actor=actor.user, group_id=night.group_id, session_id=_latest_set_id(old.plan.night),
            target=old, summary=f"Carried into the session of {_night_day(night)}: {_describe(old, night.unit)}",
        )
    # Open set pages poll their set's version: bump it so they show the closed session.
    GameSession.objects.filter(night=night).update(version=F("version") + 1)
    return plan


def _transfer(night, transfer_id) -> Transfer:
    transfer = Transfer.objects.select_related("payer", "payee").filter(pk=transfer_id, plan__night=night, plan__is_current=True).first()
    if transfer is None:
        raise RuleError("That transfer is not in this session.")
    return transfer


def _describe(transfer, unit) -> str:
    return f"{transfer.payer.display_name} → {transfer.payee_label} {money.format_amount(transfer.amount, unit)}"


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
    carry = _carried(transfer)
    if carry is not None:
        raise RuleError(f"This transfer was carried into the session of {_night_day(carry.plan.night)}. Mark it paid there.")
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


def payable_seats(night):
    """Seats a table payment can name: an accepted buy-in in a set of this session that is not canceled.

    Only these players have a result when the session closes, so only they can be in its list.
    """
    from games.models import Participant
    from ledger.models import BuyIn

    bought = BuyIn.objects.filter(participant=OuterRef("pk"), reversal__isnull=True)
    return (
        Participant.objects.filter(session__night=night).exclude(session__state=State.CANCELED)
        .filter(Exists(bought)).select_related("member")
    )


def _session_member(night, member_id) -> Member:
    if not str(member_id or "").isdecimal():
        raise RuleError("Choose two players of this session.")
    seat = payable_seats(night).filter(member_id=member_id).first()
    if seat is None:
        raise RuleError("Choose two players who bought in this session.")
    return seat.member


def _bump_sets(night) -> None:
    # Open set pages poll their set's version: bump it so they show the payment.
    GameSession.objects.filter(night=night).update(version=F("version") + 1)


@transaction.atomic
def record_table_payment(night_id, actor: Member, payer_id, payee_id, amount: int, request_id) -> Payment:
    """Record money that one player handed another at the table, while the session is open.

    It changes no result. Closing subtracts it from what is still owed (ADR 0002).
    """
    require_host(actor)
    night = games.lock_night(night_id, actor.group_id)
    repeated = Payment.objects.filter(night=night, request_id=request_id).first()
    if repeated is not None:
        return repeated
    if night.is_closed:
        raise RuleError("The session is closed. Mark a transfer paid instead.")
    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
        raise RuleError("Enter the amount paid, more than 0.")
    payer, payee = _session_member(night, payer_id), _session_member(night, payee_id)
    if payer.pk == payee.pk:
        raise RuleError("Choose two different players.")
    payment = Payment.objects.create(
        night=night, payer=payer, payee=payee, amount=amount, request_id=request_id, recorded_by=actor.user,
    )
    audit.record(
        "payment.recorded", actor=actor.user, group_id=night.group_id, session_id=_latest_set_id(night), target=payment,
        summary=f"Paid at the table: {payer.display_name} → {payee.display_name} {money.format_amount(amount, night.unit)}",
        data={"amount": amount, "unit": night.unit},
    )
    _bump_sets(night)
    return payment


@transaction.atomic
def reverse_table_payment(night_id, actor: Member, payment_id, reason: str) -> PaymentReversal:
    """Undo a table payment recorded by mistake. The payment row stays, with a reversal and its reason."""
    require_host(actor)
    night = games.lock_night(night_id, actor.group_id)
    payment = (
        Payment.objects.select_related("payer", "payee")
        .filter(pk=payment_id, night=night, transfer__isnull=True).first()
    )
    if payment is None:
        raise RuleError("That payment is not in this session.")
    if not payment.active:
        return payment.reversal  # a repeated tap
    if night.is_closed:
        raise RuleError("The session is closed. Reopen it to undo a table payment.")
    reason = " ".join((reason or "").split())[:255]
    if not reason:
        raise RuleError("Give a reason for undoing it. It stays in the log.")
    payment.active = False
    payment.save(update_fields=["active"])
    reversal = PaymentReversal.objects.create(payment=payment, reason=reason, recorded_by=actor.user)
    audit.record(
        "payment.reversed", actor=actor.user, group_id=night.group_id, session_id=_latest_set_id(night), target=payment,
        summary=f"Undid a table payment: {payment.payer.display_name} → {payment.payee.display_name} "
        f"{money.format_amount(payment.amount, night.unit)}",
        reason=reason,
    )
    _bump_sets(night)
    return reversal
