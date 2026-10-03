"""Amount arithmetic. Pure functions: integers and Decimal only, never float.

A game counts in pesos or in chips. An amount is one integer in the unit's
smallest step: centavos for pesos, whole chips for chips. A chips game has no
peso value, so nothing here converts between the two.
"""

from decimal import Decimal, InvalidOperation

PHP = "php"
CHIPS = "chips"
UNITS = (PHP, CHIPS)

PESO = "₱"
MINUS = "−"
MAX_CENTAVOS = 1_000_000_000_00  # ₱1 billion: a guard against typing errors


class MoneyError(ValueError):
    """An amount or rate that cannot be used. The message is safe to show."""


def parse_pesos(text) -> int:
    """Peso input such as ``1,000`` or ``₱250.50`` → centavos. At most two decimal places."""
    cleaned = str(text or "").replace(PESO, "").replace("PHP", "").replace(",", "").strip()
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        raise MoneyError("Enter an amount in pesos, for example 1000 or 250.50.") from None
    if not value.is_finite():
        raise MoneyError("Enter an amount in pesos, for example 1000 or 250.50.")
    centavos = value * 100
    if centavos != centavos.to_integral_value():
        raise MoneyError("Use at most two decimal places.")
    centavos = int(centavos)
    if centavos < 0:
        raise MoneyError("The amount cannot be negative.")
    if centavos > MAX_CENTAVOS:
        raise MoneyError("That amount is too large.")
    return centavos


def format_pesos(centavos: int) -> str:
    """``160000`` → ``₱1,600``; ``160050`` → ``₱1,600.50``; negatives get a minus sign."""
    sign = MINUS if centavos < 0 else ""
    pesos, cents = divmod(abs(centavos), 100)
    text = f"{pesos:,}" if cents == 0 else f"{pesos:,}.{cents:02d}"
    return f"{sign}{PESO}{text}"


def plain_pesos(centavos: int) -> str:
    """The value for an input field: ``1000`` or ``1000.50``, with no sign or separators."""
    pesos, cents = divmod(centavos, 100)
    return str(pesos) if cents == 0 else f"{pesos}.{cents:02d}"


def format_signed(centavos: int) -> str:
    """A result: ``+₱600``, ``−₱300`` or ``₱0``."""
    return f"+{format_pesos(centavos)}" if centavos > 0 else format_pesos(centavos)


def split_equal(total: int, shares: int) -> list[int]:
    """``total`` in ``shares`` equal integer parts. Units that do not divide go to the first parts."""
    if shares <= 0:
        raise MoneyError("There is nobody to share with.")
    sign = -1 if total < 0 else 1
    base, extra = divmod(abs(total), shares)
    return [sign * (base + (1 if i < extra else 0)) for i in range(shares)]


def parse_amount(text, unit: str) -> int:
    """What a person typed, as an integer amount in ``unit``."""
    if unit == PHP:
        return parse_pesos(text)
    cleaned = str(text or "").replace(",", "").replace("chips", "").strip()
    if not cleaned.isdecimal():
        raise MoneyError("Enter a whole number of chips, for example 1500.")
    chips = int(cleaned)
    if chips > MAX_CENTAVOS:
        raise MoneyError("That amount is too large.")
    return chips


def format_amount(value: int, unit: str) -> str:
    """``₱1,600`` in a pesos game, ``1,600 chips`` in a chips game. Never both."""
    if unit == PHP:
        return format_pesos(value)
    sign = MINUS if value < 0 else ""
    return f"{sign}{abs(value):,} chip{'' if abs(value) == 1 else 's'}"


def format_signed_amount(value: int, unit: str) -> str:
    """A result: ``+₱600``, ``−300 chips`` or the plain zero."""
    text = format_amount(value, unit)
    return f"+{text}" if value > 0 else text


def plain_amount(value: int, unit: str) -> str:
    """The value for an input field, with no sign, separators or unit."""
    return plain_pesos(value) if unit == PHP else str(value)
