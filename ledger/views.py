from django.contrib import messages
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from games.access import session_for
from groups.access import require_host
from groups.http import attempt, request_id_from

from . import money, services


def _pesos(request, name="amount"):
    """The posted peso amount in centavos, or None after showing an error."""
    try:
        return money.parse_pesos(request.POST.get(name, ""))
    except money.MoneyError as error:
        messages.error(request, str(error))
        return None


@require_POST
def buy_in_add(request, session_id):
    session, actor = session_for(request.user, session_id)
    require_host(actor)
    amount = _pesos(request)
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
    try:
        chips = int(request.POST.get("chips", "").replace(",", "").strip())
    except ValueError:
        messages.error(request, "Enter the number of chips, 0 or more.")
    else:
        attempt(
            request, services.record_cash_out, session.pk, actor, request.POST.get("participant_id"), chips,
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
