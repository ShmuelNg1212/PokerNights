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
from .models import SettlementPlan, Transfer

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
        raise RuleError("End play and count the chips before finalizing.")
    finalization = ledger.write_results(session, actor)
    results = list(finalization.results.select_related("participant").order_by("participant__join_order"))
    # No payment is recorded before finalization yet, so each balance equals the result.
    owed = algorithm.balances({result.participant_id: result.net_centavos for result in results})
    parties = [(result.participant_id, owed[result.participant_id]) for result in results]
    transfers = algorithm.settle(parties)
    plan = SettlementPlan.objects.create(
        finalization=finalization, proven_minimal=algorithm.is_proven_minimal(parties)
    )
    Transfer.objects.bulk_create(
        Transfer(plan=plan, position=position, payer_id=payer, payee_id=payee, amount_centavos=amount)
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
        summary=f"Finalized: {money.format_pesos(finalization.total_buy_in_centavos)} bought in, "
        f"{len(transfers)} transfer{'s' if len(transfers) != 1 else ''}",
        data={"nets": {str(r.participant_id): r.net_centavos for r in results}},
    )
    games.mark_finalized(session)
    return finalization
