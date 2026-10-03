from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from games.access import session_for
from groups.http import attempt, request_id_from

from . import services


@require_POST
def finalize(request, session_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.finalize, session.pk, actor, success="Results are final.")
    return redirect("session", session_id=session.pk)


@require_POST
def transfer_paid(request, session_id, transfer_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.mark_paid, session.pk, actor, transfer_id, request_id_from(request))
    return redirect("session", session_id=session.pk)


@require_POST
def transfer_unpaid(request, session_id, transfer_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.mark_unpaid, session.pk, actor, transfer_id)
    return redirect("session", session_id=session.pk)
