from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from groups.access import member_for, require_host
from groups.http import attempt

from . import services
from .forms import PresetForm
from .models import SettingsPreset


@require_POST
def create_table(request, group_id):
    actor = member_for(request.user, group_id)
    attempt(
        request, services.create_table, actor, request.POST.get("name", ""), request.POST.get("seat_count"),
        request.POST.get("default_preset") or None, success="Table added.",
    )
    return redirect("group", group_id=group_id)


def preset_form(request, group_id, preset_id=None):
    actor = member_for(request.user, group_id)
    require_host(actor)
    preset = None
    initial = {"game_type": "nlh"}
    if preset_id is not None:
        preset = get_object_or_404(SettingsPreset, group=actor.group, pk=preset_id, archived_at__isnull=True)
        initial = {"name": preset.name, "game_type": preset.game_type, **preset.stakes()}
    form = PresetForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        saved = attempt(request, services.save_preset, actor, form.cleaned_data, preset_id=preset_id, success="Preset saved.")
        if saved is not None:
            return redirect("group", group_id=group_id)
    return render(request, "games/preset_form.html", {"form": form, "group": actor.group, "preset": preset})
