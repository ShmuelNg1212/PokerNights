from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from games import services as games
from games.access import night_for, session_for
from django.conf import settings
from django.http import Http404

from groups import services as groups
from groups.access import member_for, require_host
from groups.http import attempt, group_settings, request_id_from
from groups.models import Member

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


def member_remove(request, group_id, member_id):
    """Ask, then remove a member from the group. The page names what stops it and any transfer still unpaid.

    It lives here because it reads seats and transfers, which the groups app cannot.
    """
    actor = member_for(request.user, group_id)
    require_host(actor)
    member = Member.objects.filter(group_id=group_id, pk=member_id, status=Member.Status.ACTIVE).first()
    if member is None:
        raise Http404("Not found")
    if request.method == "POST":
        back = " Bring them back from Removed players." if settings.ROSTER_TOOLS else ""
        if attempt(request, groups.remove_member, actor, member.pk,
                   success=f"{member.display_name} was removed.{back}") is not None:
            request.session["roster_left"] = True
            return group_settings(group_id, "players")
        return redirect("member_remove", group_id=group_id, member_id=member.pk)
    refusal = groups.removal_refusal(actor, member.pk)
    seated = games.sets_seating(member) if refusal else []
    context = {
        "group": actor.group, "member": member, "refusal": refusal, "seated": seated[0] if seated else None,
        "unpaid": [] if refusal else queries.unpaid_transfers([member.pk]), "roster_tools": settings.ROSTER_TOOLS,
    }
    return render(request, "settlement/member_remove.html", context)


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
