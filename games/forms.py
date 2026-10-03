from django import forms
from django.utils import timezone

from ledger import money

from .models import GameType, StakesFields


def amount_field(label, help_text=""):
    return forms.CharField(
        label=label, help_text=help_text,
        widget=forms.TextInput(attrs={"inputmode": "decimal", "autocomplete": "off"}),
    )


class StakesForm(forms.Form):
    """Blinds and buy-in limits, typed in the game's unit. Cleaned values are integer amounts."""

    small_blind = amount_field("Small blind")
    big_blind = amount_field("Big blind")
    min_buy_in = amount_field("Minimum buy-in")
    max_buy_in = amount_field("Maximum buy-in")
    default_buy_in = amount_field("Usual buy-in", "The amount that the buy-in button starts with.")

    def __init__(self, *args, unit=money.PHP, **kwargs):
        initial = dict(kwargs.pop("initial", None) or {})
        for name in StakesFields.STAKES_FIELDS:
            if isinstance(initial.get(name), int):
                initial[name] = money.plain_amount(initial[name], initial.get("unit", unit))
        super().__init__(*args, initial=initial, **kwargs)
        self.unit = unit

    def chosen_unit(self, cleaned) -> str:
        return self.unit

    def clean(self):
        cleaned = super().clean()
        unit = self.chosen_unit(cleaned)
        for name in StakesFields.STAKES_FIELDS:
            if name not in cleaned:
                continue
            try:
                cleaned[name] = money.parse_amount(cleaned[name], unit)
            except money.MoneyError as error:
                self.add_error(name, str(error))
        return cleaned


class PresetForm(StakesForm):
    name = forms.CharField(label="Preset name", max_length=60)
    game_type = forms.ChoiceField(label="Game", choices=GameType.choices)

    field_order = ["name", "game_type"]


class SessionForm(StakesForm):
    table_id = forms.ChoiceField(label="Table")
    game_date = forms.DateField(label="Date", widget=forms.DateInput(attrs={"type": "date"}))
    location = forms.CharField(label="Location", max_length=120, required=False)
    game_type = forms.ChoiceField(label="Game", choices=GameType.choices)

    field_order = ["table_id", "game_date", "location", "game_type"]

    def __init__(self, *args, tables=(), **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["table_id"].choices = [(table.pk, f"{table.name} ({table.seat_count} seats)") for table in tables]
        self.fields["game_date"].initial = timezone.localdate

    def clean_table_id(self):
        return int(self.cleaned_data["table_id"])
