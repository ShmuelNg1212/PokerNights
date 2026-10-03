import uuid

from django import template
from django.utils.html import format_html

from ledger import money

register = template.Library()


@register.filter
def amount(value, unit):
    """An amount in the game's unit: ``{{ line.buy_in_total|amount:session.unit }}``."""
    return "" if value is None else money.format_amount(value, unit)


@register.filter
def signed_amount(value, unit):
    return "" if value is None else money.format_signed_amount(value, unit)


@register.filter
def sign_class(value):
    """CSS class for a result: plus, minus or nothing."""
    if not value:
        return ""
    return "plus" if value > 0 else "minus"


@register.simple_tag
def request_id_field():
    """A hidden field that identifies one form, so a repeated submission records nothing twice."""
    return format_html('<input type="hidden" name="request_id" value="{}">', uuid.uuid4())
