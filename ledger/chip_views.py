"""The denomination input adapter for the existing final-count services."""
import uuid

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from games import chips
from games.access import session_for
from groups.errors import RuleError
from groups.http import request_id_from

from . import queries, services


def denominations(night):
    return chips.named(night.chip_values)


def form_context(session, participant, actor, draft=None):
    draft = draft or {}
    typed = draft.get("quantities", {})
    rows = [{**row, "quantity": typed.get(row["id"], "")} for row in denominations(session.night)]
    return {"rows": rows, "participant": participant, "key": f"chip-count-{participant.pk}",
            "revision": draft.get("revision", session.night.chip_values_revision),
            "request_id": uuid.uuid4(), "host": actor.is_host, "inline": True,
            "error": draft.get("error", ""), "empty_stack": draft.get("empty_stack", False)}


def count(request, session_id, participant_id):
    session, actor = session_for(request.user, session_id)
    participant = get_object_or_404(session.participants.select_related("member"), pk=participant_id)
    if not actor.is_host and (participant.member_id != actor.pk or not settings.PLAYER_ENTRIES):
        raise Http404("Not found")
    if not session.night.chip_values:
        messages.info(request, "The host has not set chip values for this session.")
        return redirect("session", session_id=session.pk)
    draft = None
    if request.method == "POST":
        revision = request.POST.get("chip_revision", "")
        # Keep duplicate IDs visible to the service; never collapse the posted rows to a dict.
        pairs = [(name[4:], value) for name, values in request.POST.lists()
                 if name.startswith("qty_") for value in values]
        empty = request.POST.get("empty_stack") == "1"
        try:
            options = {"chips": pairs, "chip_revision": int(revision) if revision.isdecimal() else -1,
                       "empty_stack": empty}
            if actor.is_host:
                services.confirm_count(session.pk, actor, participant.pk, None, request_id_from(request), **options)
            else:
                services.enter_count(session.pk, actor, None, request_id_from(request), **options)
        except RuleError as refused:
            draft = {"quantities": dict(pairs), "revision": revision, "empty_stack": empty, "error": str(refused)}
            if request.headers.get("X-Answer-In-Place") == f"/s/{session.pk}/":
                drafts = request.session.get("chip_count_drafts", {})
                drafts[str(participant.pk)] = draft
                request.session["chip_count_drafts"] = drafts
                messages.error(request, str(refused))
                return redirect("session", session_id=session.pk)
        else:
            messages.success(request, "Count confirmed." if actor.is_host else "Count sent to the host.")
            return redirect("session", session_id=session.pk)
    line = queries.summary(session).line_for(participant.pk)
    chip_form = form_context(session, participant, actor, draft)
    chip_form["inline"] = False
    return render(request, "ledger/chip_count.html", {
        "session": session, "unit": session.unit, "me": actor, "line": line,
        "chip_form": chip_form,
    })
