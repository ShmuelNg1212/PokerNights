from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from games import services as games
from games.access import night_for, session_for
from django.conf import settings
from django.http import Http404

from groups import services as groups
from groups.access import member_for, require_host
from groups.errors import RuleError
from groups.http import attempt, group_settings, request_id_from
from groups.models import Member
from ledger import money

from . import queries, services


@require_POST
def finalize(request, session_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.finalize, session.pk, actor, success=f"Set {session.set_number} is final.")
    return redirect("session", session_id=session.pk)


@require_POST
def close_night(request, night_id):
    night, actor = night_for(request.user, night_id)
    attempt(
        request, services.close_night, night.pk, actor, request.POST.getlist("carry"),
        success="Session closed.",
    )
    return redirect("night", night_id=night.pk)


@require_POST
def reopen_set(request, session_id):
    session, actor = session_for(request.user, session_id)
    attempt(request, services.reopen_set, session.pk, actor, request.POST.get("reason", ""),
            success=f"Set {session.set_number} is counting up again.")
    return redirect("session", session_id=session.pk)


@require_POST
def reopen_night(request, night_id):
    night, actor = night_for(request.user, night_id)
    attempt(request, services.reopen_night, night.pk, actor, request.POST.get("reason", ""),
            success="The session is open again.")
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


def _back_to(night, request):
    """The set page the host came from, when it is a set of this session; else the session page."""
    from games.models import GameSession

    set_id = request.POST.get("from_set") or request.GET.get("from_set")
    if set_id and str(set_id).isdecimal() and GameSession.objects.filter(pk=set_id, night=night).exists():
        return int(set_id)
    return None


def _prefill(query, unit) -> dict:
    """The form's first values. A left player's link sends ``leaver`` and their set figure ``net``, an
    integer in the game's unit: a winner is paid, a loser pays. The host chooses the other player."""
    values = {"payer": "", "payee": "", "amount": ""}
    leaver, net = query.get("leaver", ""), query.get("net", "")
    if leaver.isdecimal() and net.lstrip("-").isdecimal() and int(net):
        values["payee" if int(net) > 0 else "payer"] = leaver
        values["amount"] = money.plain_amount(abs(int(net)), unit)
    return values


def table_payment(request, night_id):
    """Record a payment made at the table while the session is open (ADR 0002).

    The session page opens the form in a sheet; this page is its fallback, and where a left
    player's link on the set page leads, with the figures filled in.
    """
    night, actor = night_for(request.user, night_id)
    require_host(actor)
    players = queries.session_players(night)
    from_set = _back_to(night, request)
    error = ""
    if request.method == "POST":
        values = {key: request.POST.get(key, "") for key in ("payer", "payee", "amount")}
        try:
            amount = money.parse_amount(values["amount"], night.unit)
        except money.MoneyError as refused:
            error = str(refused)
        else:
            try:
                services.record_table_payment(
                    night.pk, actor, values["payer"], values["payee"], amount, request_id_from(request)
                )
            except RuleError as refused:
                error = str(refused)
            else:
                messages.success(request, "Payment recorded.")
                if from_set:
                    return redirect("session", session_id=from_set)
                return redirect("night", night_id=night.pk)
    else:
        values = _prefill(request.GET, night.unit)
    context = {
        "night": night, "unit": night.unit, "players": players, "values": values, "error": error,
        "from_set": from_set, "closed": night.is_closed,
    }
    return render(request, "settlement/table_payment.html", context, status=422 if error else 200)


@require_POST
def table_payment_undo(request, night_id, payment_id):
    night, actor = night_for(request.user, night_id)
    attempt(request, services.reverse_table_payment, night.pk, actor, payment_id, request.POST.get("reason", ""),
            success="Payment undone.")
    return redirect("night", night_id=night.pk)


def night_archive(request, night_id):
    """Confirm, then archive. The confirmation names any transfer that is still unpaid."""
    night, actor = night_for(request.user, night_id)
    require_host(actor)
    if request.method == "POST":
        if attempt(request, games.archive_night, night.pk, actor,
                   success="Session archived.") is not None:
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
