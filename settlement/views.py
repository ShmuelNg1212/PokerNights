from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from games import services as games
from games.access import night_for, session_for
from groups.access import require_host
from groups.http import attempt, request_id_from

from . import queries, services


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


def night_archive(request, night_id):
    """Confirm, then archive. The confirmation names any transfer that is still unpaid."""
    night, actor = night_for(request.user, night_id)
    require_host(actor)
    if request.method == "POST":
        if attempt(request, games.archive_night, night.pk, actor,
                   success="Session archived. A host can restore it from Archived sessions.") is not None:
            return redirect("group", group_id=night.group_id)
        return redirect("night", night_id=night.pk)
    context = {"night": night, "mode": "archive", "unit": night.unit, "unpaid": queries.unpaid_in(night),
               "unfinished": games.unfinished_sets(night)}
    return render(request, "settlement/night_manage.html", context)


@require_POST
def night_restore(request, night_id):
    night, actor = night_for(request.user, night_id)
    attempt(request, games.restore_night, night.pk, actor, success="Session restored.")
    return redirect("night", night_id=night.pk)


def night_delete(request, night_id):
    """Confirm, then delete a session that never held money."""
    night, actor = night_for(request.user, night_id)
    require_host(actor)
    if request.method == "POST":
        group_id, name = night.group_id, str(night)
        try:
            games.delete_night(night.pk, actor)
        except games.RuleError as refused:
            messages.error(request, str(refused))
            return redirect("night", night_id=night.pk)
        messages.success(request, f"Deleted the session {name}.")
        return redirect("group", group_id=group_id)
    context = {"night": night, "mode": "delete", "unit": night.unit, "has_records": games.night_has_records(night),
               "unfinished": games.unfinished_sets(night)}
    return render(request, "settlement/night_manage.html", context)
