from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from games.access import night_for, session_for
from groups.http import attempt, request_id_from

from . import services


@require_POST
def finalize(request, session_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.finalize, session.pk, actor, success=f"The results of set {session.set_number} are final.")
    return redirect("session", session_id=session.pk)


@require_POST
def close_night(request, night_id):
    night, actor = night_for(request.user, night_id)
    attempt(request, services.close_night, night.pk, actor, success="The session is closed. Transfers are listed below.")
    return redirect("night", night_id=night.pk)


@require_POST
def transfer_paid(request, night_id, transfer_id):
    night, actor = night_for(request.user, night_id)
    attempt(request, services.mark_paid, night.pk, actor, transfer_id, request_id_from(request))
    return redirect("night", night_id=night.pk)


@require_POST
def transfer_unpaid(request, night_id, transfer_id):
    night, actor = night_for(request.user, night_id)
    attempt(request, services.mark_unpaid, night.pk, actor, transfer_id)
    return redirect("night", night_id=night.pk)
