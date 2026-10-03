from django.contrib import messages
import uuid

from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from games.access import session_for
from groups.access import require_host
from groups.http import attempt, request_id_from

from groups.errors import RuleError

from . import money, queries, services


def _amount(request, session, name="amount"):
    """The posted amount in the session's unit, or None after showing an error."""
    try:
        return money.parse_amount(request.POST.get(name, ""), session.unit)
    except money.MoneyError as error:
        messages.error(request, str(error))
        return None


@require_POST
def buy_in_add(request, session_id):
    session, actor = session_for(request.user, session_id)
    require_host(actor)
    amount = _amount(request, session)
    if amount is not None:
        attempt(
            request, services.record_buy_in, session.pk, actor, request.POST.get("participant_id"), amount,
            request_id_from(request),
        )
    return redirect("session", session_id=session.pk)


@require_POST
def buy_in_reverse(request, session_id, buy_in_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.reverse_buy_in, session.pk, actor, buy_in_id, request.POST.get("reason", ""), success="Buy-in reversed.")
    return redirect("session", session_id=session.pk)


@require_POST
def cash_out_add(request, session_id):
    session, actor = session_for(request.user, session_id)
    require_host(actor)
    amount = _amount(request, session)
    if amount is not None:
        attempt(
            request, services.record_cash_out, session.pk, actor, request.POST.get("participant_id"), amount,
            request_id_from(request), left=request.POST.get("left") == "1",
        )
    return redirect("session", session_id=session.pk)


@require_POST
def cash_out_reverse(request, session_id, cash_out_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.reverse_cash_out, session.pk, actor, cash_out_id, request.POST.get("reason", ""), success="Cash-out reversed.")
    return redirect("session", session_id=session.pk)


@require_POST
def override_add(request, session_id):
    session, actor = session_for(request.user, session_id)
    absorber = request.POST.get("absorber", "")
    mode = "equal" if absorber == "equal" else "player"
    attempt(
        request, services.record_override, session.pk, actor, request.POST.get("note", ""), mode, absorber,
        request_id_from(request), success="Override recorded.",
    )
    return redirect("session", session_id=session.pk)


@require_POST
def override_void(request, session_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.void_override, session.pk, actor, success="Override removed.")
    return redirect("session", session_id=session.pk)


DRAFTS_KEY = "count_drafts"


def _typed_counts(request) -> dict:
    """``{participant_id: text}`` for every count field that holds something."""
    typed = {}
    for name, value in request.POST.items():
        if name.startswith("count_") and name[6:].isdecimal() and value.strip():
            typed[int(name[6:])] = value.strip()
    # The earlier one-row form: participant_id and amount.
    if request.POST.get("participant_id", "").isdecimal() and request.POST.get("amount", "").strip():
        typed[int(request.POST["participant_id"])] = request.POST["amount"].strip()
    return typed


@require_POST
def count_confirm(request, session_id):
    """Confirm every final count that is typed on the set page, in one action.

    If anything is refused, nothing is saved and the typed values are shown
    again, so the host never has to type them twice.
    """
    session, actor = session_for(request.user, session_id)
    require_host(actor)
    typed = _typed_counts(request)
    names = dict(session.participants.values_list("pk", "member__display_name"))
    amounts, error = {}, ""
    if not typed:
        # An empty field is never read as zero.
        error = "Enter the final count. Type 0 for a player who has nothing left."
    for participant_id, text in typed.items():
        try:
            amounts[participant_id] = money.parse_amount(text, session.unit)
        except money.MoneyError as refused:
            error = f"{names.get(participant_id, 'A player')}: {refused} Nothing was saved."
            break
    if not error:
        try:
            written = services.confirm_counts(session.pk, actor, amounts, request_id_from(request))
        except RuleError as refused:
            error = f"{refused} Nothing was saved."
    drafts = request.session.get(DRAFTS_KEY, {})
    if error:
        messages.error(request, error)
        drafts[str(session.pk)] = {str(pid): text for pid, text in typed.items()}
    else:
        drafts.pop(str(session.pk), None)
        count = len(written)
        if count:
            messages.success(request, f"{count} count{'' if count == 1 else 's'} confirmed.")
    request.session[DRAFTS_KEY] = drafts
    return redirect("session", session_id=session.pk)


@require_POST
def count_clear(request, session_id, participant_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.clear_count, session.pk, actor, participant_id, success="Count cleared.")
    return redirect("session", session_id=session.pk)


def cash_out_counted(request, session_id):
    """Review the players with confirmed counts, then cash them all out with one confirmation."""
    session, actor = session_for(request.user, session_id)
    require_host(actor)
    error = ""
    if request.method == "POST":
        try:
            batch = services.cash_out_counted(
                session.pk, actor, request.POST.getlist("count_id"), request_id_from(request)
            )
        except RuleError as refused:
            error = str(refused)  # nothing was recorded; show a fresh review below
        else:
            done = batch.cash_outs.count()
            waiting = len(queries.summary(session).awaiting_lines) + len(queries.summary(session).ready_lines)
            rest = (
                f"{waiting} awaiting final count{'' if waiting == 1 else 's'}" if waiting
                else "everyone is cashed out"
            )
            messages.success(request, f"{done} player{'' if done == 1 else 's'} cashed out; {rest}.")
            return redirect("session", session_id=session.pk)
    session.refresh_from_db()
    if session.state != services.State.RECONCILIATION:
        messages.error(request, "Counted players are cashed out after play has ended.")
        return redirect("session", session_id=session.pk)
    summary = queries.summary(session)
    ready = summary.ready_lines
    context = {
        "session": session,
        "unit": session.unit,
        "error": error,
        "ready": ready,
        "participants": [line.participant for line in summary.lines],
        "awaiting": summary.awaiting_lines,
        "cashed_out": summary.cashed_out_lines,
        "batch_total": sum(line.count.amount for line in ready),
        "summary": summary,
        "after_batch": summary.cashed_out + sum(line.count.amount for line in ready),
        "request_id": uuid.uuid4(),
    }
    return render(request, "ledger/cash_out_counted.html", context)
