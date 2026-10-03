from django import forms
from django.core.exceptions import ValidationError

from ledger import money

from .models import GameType


class PesoField(forms.CharField):
    """A peso amount typed by a person. The cleaned value is integer centavos."""

    def __init__(self, **kwargs):
        kwargs.setdefault("widget", forms.TextInput(attrs={"inputmode": "decimal", "autocomplete": "off"}))
        super().__init__(**kwargs)

    def to_python(self, value):
        value = super().to_python(value)
        if value in self.empty_values:
            return None
        try:
            return money.parse_pesos(value)
        except money.MoneyError as error:
            raise ValidationError(str(error)) from None

    def prepare_value(self, value):
        if isinstance(value, int):
            pesos, cents = divmod(value, 100)
            return str(pesos) if cents == 0 else f"{pesos}.{cents:02d}"
        return value


class StakesForm(forms.Form):
    small_blind_centavos = PesoField(label="Small blind (₱)")
    big_blind_centavos = PesoField(label="Big blind (₱)")
    min_buy_in_centavos = PesoField(label="Minimum buy-in (₱)")
    max_buy_in_centavos = PesoField(label="Maximum buy-in (₱)")
    default_buy_in_centavos = PesoField(label="Usual buy-in (₱)")
    chips_per_buy_in = forms.IntegerField(
        label="Chips for the usual buy-in", min_value=1,
        help_text="For example 10000 chips for ₱1,000. This sets the value of one chip.",
    )


class PresetForm(StakesForm):
    name = forms.CharField(label="Preset name", max_length=60)
    game_type = forms.ChoiceField(label="Game", choices=GameType.choices)

    field_order = ["name", "game_type"]
