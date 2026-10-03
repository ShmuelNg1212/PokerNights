"""Money and chip arithmetic. Pure functions: integers and Decimal only, never float.

Money is integer centavos. Chips are integer chip units. A chip rate is the
pair ``(rate_centavos, rate_chips)``: ``rate_chips`` chips are worth
``rate_centavos`` centavos. A chip is never assumed to be a peso.
"""

from decimal import Decimal, InvalidOperation
from math import gcd

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


def reduce_rate(centavos: int, chips: int) -> tuple[int, int]:
    """The chip rate in lowest terms, e.g. ₱1,000 for 10,000 chips → ``(10, 1)``."""
    if centavos <= 0 or chips <= 0:
        raise MoneyError("The buy-in amount and its chips must both be more than zero.")
    divisor = gcd(centavos, chips)
    return centavos // divisor, chips // divisor


def chips_for_amount(amount_centavos: int, rate: tuple[int, int]) -> int:
    """Chips issued for an amount at ``rate``. The result must be a whole number of chips."""
    rate_centavos, rate_chips = rate
    chips, remainder = divmod(amount_centavos * rate_chips, rate_centavos)
    if remainder:
        raise MoneyError(
            f"{format_pesos(amount_centavos)} does not buy a whole number of chips at this session's chip rate."
        )
    return chips


def value_floor(chips: int, rate: tuple[int, int]) -> tuple[int, bool]:
    """Centavo value of ``chips`` rounded down, and whether that value is exact."""
    rate_centavos, rate_chips = rate
    value, remainder = divmod(chips * rate_centavos, rate_chips)
    return value, remainder == 0


def allocate(chips: list[int], rate: tuple[int, int]) -> list[int]:
    """Centavo value of each chip count, by the largest-remainder rule.

    Each count gets its exact value rounded down. The centavos left over go one
    each to the counts with the largest fractional parts; ties go to the earlier
    position. The results always sum to the exact total, so no centavo is
    created or lost. The total must itself be a whole number of centavos.
    """
    rate_centavos, rate_chips = rate
    total, total_remainder = divmod(sum(chips) * rate_centavos, rate_chips)
    if total_remainder:
        raise MoneyError("The chip total is not worth a whole number of centavos.")
    parts = [divmod(count * rate_centavos, rate_chips) for count in chips]
    values = [floor for floor, _ in parts]
    leftover = total - sum(values)
    by_remainder = sorted(range(len(chips)), key=lambda i: (-parts[i][1], i))
    for i in by_remainder[:leftover]:
        values[i] += 1
    return values


def split_equal(total: int, shares: int) -> list[int]:
    """``total`` in ``shares`` equal integer parts. Units that do not divide go to the first parts."""
    if shares <= 0:
        raise MoneyError("There is nobody to share with.")
    sign = -1 if total < 0 else 1
    base, extra = divmod(abs(total), shares)
    return [sign * (base + (1 if i < extra else 0)) for i in range(shares)]


# --- Amounts in a game's unit --------------------------------------------------
#
# A game counts in pesos or in chips. An amount is one integer in the unit's
# smallest step: centavos for pesos, whole chips for chips. A chips game has no
# peso value: nothing here converts between the two.


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
