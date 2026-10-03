from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from games.access import session_for
from groups.access import require_host
from groups.http import attempt, request_id_from

from . import money, services


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


@require_POST
def count_confirm(request, session_id):
    session, actor = session_for(request.user, session_id)
    require_host(actor)
    if not request.POST.get("amount", "").strip():
        # An empty field is never read as zero.
        messages.error(request, "Enter the final count. Type 0 for a player who has nothing left.")
        return redirect("session", session_id=session.pk)
    amount = _amount(request, session)
    if amount is not None:
        attempt(
            request, services.confirm_count, session.pk, actor, request.POST.get("participant_id"), amount,
            request_id_from(request),
        )
    return redirect("session", session_id=session.pk)


@require_POST
def count_clear(request, session_id, participant_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.clear_count, session.pk, actor, participant_id, success="Count cleared.")
    return redirect("session", session_id=session.pk)
