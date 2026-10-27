"""Session chip-value setup. Writes go through the games service."""
import uuid

from django import forms
from django.contrib import messages
from django.forms import formset_factory
from django.shortcuts import redirect, render

from groups.access import require_host
from groups.errors import RuleError
from groups.http import request_id_from
from ledger import money

from . import chips, services
from .access import night_for


class ChipValueForm(forms.Form):
    colour = forms.ChoiceField(label="Colour", choices=())
    label = forms.CharField(label="Label (optional)", max_length=40, required=False)
    value = forms.CharField(label="Value", widget=forms.TextInput(attrs={
        "inputmode": "decimal", "autocomplete": "off",
    }))

    def __init__(self, *args, unit="php", **kwargs):
        super().__init__(*args, **kwargs)
        self.unit = unit
        self.fields["colour"].choices = [("", "Choose a colour")] + [(key, name) for key, name, _ in chips.COLOURS]
        self.fields["value"].label = "Value (₱)" if unit == "php" else "Value (chip units)"
        if unit == "chips":
            self.fields["value"].widget.attrs["inputmode"] = "numeric"

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


def values(request, night_id):
    night, actor = night_for(request.user, night_id)
    require_host(actor)
    locked = bool(night.chip_values_locked_at or night.is_closed or night.is_archived)
    initial = [{"colour": row["colour"], "label": row["label"],
                "value": money.plain_amount(row["value"], night.unit)} for row in night.chip_values]
    formset = ChipValueForms(request.POST if request.method == "POST" else None,
                             initial=initial, prefix="chips", form_kwargs={"unit": night.unit})
    revision = request.POST.get("revision", str(night.chip_values_revision))
    request_id = request_id_from(request) if request.method == "POST" else uuid.uuid4()
    error = ""
    if request.method == "POST":
        if request.POST.get("intent") == "add":
            # The same add-row control works without JavaScript. It does not save anything.
            rows = [{name: form[name].value() for name in ("colour", "label", "value")}
                    for form in formset.forms if not form["DELETE"].value()]
            if len(rows) < 12:
                rows.append({})
            formset = ChipValueForms(initial=rows, prefix="chips", form_kwargs={"unit": night.unit})
        elif formset.is_valid():
            try:
                services.set_chip_values(night.pk, actor,
                    [{key: row[key] for key in ("colour", "label", "value")}
                     for row in formset.cleaned_data if row and not row.get("DELETE")],
                    request_id, revision=int(revision) if str(revision).isdecimal() else -1)
            except RuleError as refused:
                error = str(refused)
            else:
                messages.success(request, "Chip values saved for every set in this session.")
                return redirect("night", night_id=night.pk)
    return render(request, "games/chip_values.html", {
        "night": night, "unit": night.unit, "me": actor, "formset": formset, "error": error,
        "locked": locked, "revision": revision, "request_id": request_id,
        "colours": [{"key": key, "hex": colour} for key, _, colour in chips.COLOURS],
    })
