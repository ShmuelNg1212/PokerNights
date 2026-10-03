import uuid

from django import template
from django.utils.html import format_html

from ledger import money

register = template.Library()


@register.filter
def peso(centavos):
    """Centavos → ``₱1,600``. Empty for None."""
    return "" if centavos is None else money.format_pesos(centavos)


@register.filter
def signed_peso(centavos):
    return "" if centavos is None else money.format_signed(centavos)


@register.filter
def chips(count):
    """A chip count with thousands separators and no currency sign."""
    return "" if count is None else f"{count:,}".replace("-", money.MINUS)


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
