from django import template

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
