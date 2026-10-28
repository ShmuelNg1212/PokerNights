"""Session chip-value setup. Writes go through the games service."""
import uuid

from django import forms
from django.contrib import messages
from django.forms import formset_factory
from django.shortcuts import get_object_or_404, redirect, render

from groups.access import member_for, require_host
from groups.errors import RuleError
from groups.http import group_settings, request_id_from
from ledger import money

from . import chips, services
from .access import night_for
from .forms import unit_field
from .models import ChipPreset, Unit


class ChipValueForm(forms.Form):
    colour = forms.ChoiceField(label="Colour", choices=())
    label = forms.CharField(label="Label (optional)", max_length=40, required=False)
    value = forms.CharField(label="Value", widget=forms.TextInput(attrs={
        "inputmode": "decimal", "autocomplete": "off", "data-numpad": "pesos",
    }))

    def __init__(self, *args, unit="php", choosable=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.unit = unit
        self.fields["colour"].choices = [("", "Choose a colour")] + [(key, name) for key, name, _ in chips.COLOURS]
        if choosable:
            # A preset's unit is chosen in the same form: the keys follow that choice (numpad.js "amount").
            self.fields["value"].widget.attrs["data-numpad"] = "amount"
        elif unit == "chips":
            self.fields["value"].label = "Value (chip units)"
            self.fields["value"].widget.attrs.update({"inputmode": "numeric", "data-numpad": "chips"})
        else:
            self.fields["value"].label = "Value (₱)"

    def clean_value(self):
        try:
            value = money.parse_amount(self.cleaned_data["value"], self.unit)
        except money.MoneyError as error:
            raise forms.ValidationError(str(error)) from None
        if value <= 0:
            raise forms.ValidationError("Use a value greater than zero.")
        return value


ChipValueForms = formset_factory(ChipValueForm, extra=0, min_num=1, max_num=12,
                                validate_min=True, validate_max=True, can_delete=True, absolute_max=48)


def _initial(values, unit):
    return [{"colour": row["colour"], "label": row["label"], "value": money.plain_amount(row["value"], unit)} for row in values]


def _typed(formset):
    """The rows as typed, removed rows left out: the add-row control redraws them without saving."""
    return [{name: form[name].value() for name in ("colour", "label", "value")}
            for form in formset.forms if not form["DELETE"].value()]


def _cleaned(formset):
    return [{key: row[key] for key in ("colour", "label", "value")}
            for row in formset.cleaned_data if row and not row.get("DELETE")]


def _with_row(rows):
    return rows + [{}] if len(rows) < 12 else rows


def values(request, night_id):
    night, actor = night_for(request.user, night_id)
    require_host(actor)
    locked = bool(night.chip_values_locked_at or night.is_closed or night.is_archived)
    post = request.POST if request.method == "POST" else None
    intent = post.get("intent", "") if post else ""
    kwargs = {"prefix": "chips", "form_kwargs": {"unit": night.unit}}
    formset = ChipValueForms(post, initial=_initial(night.chip_values, night.unit), **kwargs)
    revision = request.POST.get("revision", str(night.chip_values_revision))
    request_id = request_id_from(request) if post else uuid.uuid4()
    presets = [] if locked else list(services.chip_presets_for(actor.group, night.unit))
    from_preset = next((p for p in presets if post and str(p.pk) == post.get("from_preset")), None)
    error = preset_error = saved_preset = ""
    preset_name = post.get("preset_name", "") if post else ""
    if intent == "add":
        # The same add-row control works without JavaScript. It does not save anything.
        formset = ChipValueForms(initial=_with_row(_typed(formset)), **kwargs)
    elif intent == "preset":
        # Filling saves nothing: the host checks the rows, then saves them as this session's copy.
        from_preset = next((p for p in presets if str(p.pk) == post.get("preset")), None)
        if from_preset is None:
            preset_error = "Choose a preset from this group with this session's unit."
            formset = ChipValueForms(initial=_initial(night.chip_values, night.unit), **kwargs)
        else:
            formset = ChipValueForms(initial=_initial(from_preset.values, night.unit), **kwargs)
    elif intent == "save_preset":
        rows = night.chip_values if locked else _cleaned(formset) if formset.is_valid() else None
        if rows is not None:
            try:
                saved = services.save_chip_preset(actor, {"name": preset_name, "unit": night.unit, "values": rows}, request_id)
            except RuleError as refused:
                preset_error = str(refused)
            else:
                saved_preset, preset_name, request_id = saved.name, "", uuid.uuid4()
                presets = [] if locked else list(services.chip_presets_for(actor.group, night.unit))
    elif post and formset.is_valid():
        try:
            services.set_chip_values(night.pk, actor, _cleaned(formset), request_id,
                revision=int(revision) if str(revision).isdecimal() else -1,
                preset=from_preset.name if from_preset else None)
        except RuleError as refused:
            error = str(refused)
        else:
            messages.success(request, "Chip values saved for every set in this session.")
            return redirect("night", night_id=night.pk)
    return render(request, "games/chip_values.html", {
        "night": night, "unit": night.unit, "me": actor, "formset": formset, "error": error,
        "locked": locked, "revision": revision, "request_id": request_id, "intent": intent,
        "presets": presets, "from_preset": from_preset, "preset_error": preset_error,
        "preset_name": preset_name, "saved_preset": saved_preset,
        "preset_fill": {p.pk: {"name": p.name, "rows": _initial(p.values, night.unit)} for p in presets},
        "colours": [{"key": key, "hex": colour} for key, _, colour in chips.COLOURS],
    })


class ChipPresetForm(forms.Form):
    name = forms.CharField(label="Preset name", max_length=60)
    unit = unit_field()


def preset(request, group_id, preset_id=None):
    """A host's page for one group chip preset: create, edit or archive."""
    actor = member_for(request.user, group_id)
    require_host(actor)
    current = None
    if preset_id is not None:
        current = get_object_or_404(ChipPreset, group=actor.group, pk=preset_id, archived_at__isnull=True)
    post = request.POST if request.method == "POST" else None
    intent = post.get("intent", "") if post else ""
    request_id = request_id_from(request) if post else uuid.uuid4()
    if current and intent == "archive":
        try:
            services.archive_chip_preset(actor, current.pk, request_id)
        except RuleError as refused:
            messages.error(request, str(refused))
        else:
            messages.success(request, f"Archived {current.name}. Sessions keep their chip values.")
        return group_settings(group_id, "chip-presets")
    saved_unit = current.unit if current else Unit.PHP
    unit = post.get("unit") if post and post.get("unit") in Unit.values else saved_unit
    kwargs = {"prefix": "chips", "form_kwargs": {"unit": unit, "choosable": True}}
    meta = ChipPresetForm(post if intent != "add" else None,
                          initial={"name": post.get("name") if post else current and current.name, "unit": unit})
    formset = ChipValueForms(post, initial=_initial(current.values, saved_unit) if current else [{}], **kwargs)
    error = ""
    if intent == "add":
        formset = ChipValueForms(initial=_with_row(_typed(formset)), **kwargs)
    elif post and meta.is_valid() and formset.is_valid():
        try:
            services.save_chip_preset(actor, {"name": meta.cleaned_data["name"], "unit": unit,
                                              "values": _cleaned(formset)}, request_id, preset_id=preset_id)
        except RuleError as refused:
            error = str(refused)
        else:
            messages.success(request, "Chip preset saved.")
            return group_settings(group_id, "chip-presets")
    return render(request, "games/chip_preset.html", {
        "group": actor.group, "preset": current, "form": meta, "formset": formset, "error": error,
        "request_id": request_id, "colours": [{"key": key, "hex": colour} for key, _, colour in chips.COLOURS],
    })
