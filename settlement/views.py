from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from games.access import session_for
from groups.http import attempt

from . import services


@require_POST
def finalize(request, session_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.finalize, session.pk, actor, success="Results are final.")
    return redirect("session", session_id=session.pk)
