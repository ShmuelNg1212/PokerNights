"""Chip denominations in a session's unit. No currency conversion."""
from groups.errors import RuleError

MAX_AMOUNT = 100_000_000_000
COLOURS = (
    ('white', 'White', '#ece8df'), ('red', 'Red', '#b6444d'),
    ('blue', 'Blue', '#467cc2'), ('green', 'Green', '#469764'),
    ('black', 'Black', '#333333'), ('purple', 'Purple', '#9361b1'),
    ('yellow', 'Yellow', '#e4bd48'), ('orange', 'Orange', '#d48d48'),
    ('pink', 'Pink', '#dd86a1'), ('brown', 'Brown', '#916743'),
    ('grey', 'Grey', '#b4b1a6'), ('teal', 'Teal', '#70b9bd'),
)


def denominations(rows):
    """Validate a host's assignment rows and return their canonical representation."""
    if not isinstance(rows, (list, tuple)) or not 1 <= len(rows) <= 12:
        raise RuleError('Add between 1 and 12 chip colours.')
    colours, cleaned = {key for key, _, _ in COLOURS}, []
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise RuleError('Check each chip colour and value.')
        colour, value = row.get('colour'), row.get('value')
        if not isinstance(colour, str) or colour not in colours or colour in seen:
            raise RuleError('Choose a different colour for each chip.')
        if type(value) is not int or not 0 < value <= MAX_AMOUNT:
            raise RuleError('Each chip value must be more than zero and within the amount limit.')
        label = row.get('label', '')
        if not isinstance(label, str) or len(label.strip()) > 40:
            raise RuleError('Use at most 40 characters for a chip label.')
        seen.add(colour)
        cleaned.append({'id': colour, 'colour': colour, 'label': label.strip(), 'value': value})
    return cleaned


def named(values):
    """Saved rows with what a screen shows: the label or colour name, the colour name and its swatch."""
    palette = {key: (name, colour) for key, name, colour in COLOURS}
    return [{**row, "name": row["label"] or palette[row["colour"]][0],
             "colour_name": palette[row["colour"]][0], "hex": palette[row["colour"]][1]}
            for row in values]


def calculate(values, quantities, *, empty_stack=False):
    """Calculate a stack in integer units and retain its complete denomination breakdown."""
    if not values:
        raise RuleError('Ask the host to set this session\'s chip values first.')
    if not isinstance(quantities, (list, tuple)):
        raise RuleError('Enter a whole number of chips for each colour.')
    saved, entered = {row['id']: row for row in values}, {}
    explicit = False
    for row in quantities:
        if not isinstance(row, (list, tuple)) or len(row) != 2:
            raise RuleError('Check each chip quantity.')
        key, quantity = row
        if not isinstance(key, str) or key not in saved or key in entered:
            raise RuleError('The chip colours do not match this session. Reload and check them.')
        if type(quantity) is int:
            number = quantity
            explicit = True
        elif isinstance(quantity, str):
            text = quantity.strip()
            explicit = explicit or bool(text)
            if not text:
                number = 0
            elif text.isascii() and text.isdecimal() and len(text) <= 12:
                number = int(text)
            else:
                raise RuleError('Enter a whole number of chips, 0 or more.')
        else:
            raise RuleError('Enter a whole number of chips, 0 or more.')
        if not 0 <= number <= MAX_AMOUNT:
            raise RuleError('That chip quantity is too large or negative.')
        entered[key] = number
    if empty_stack and any(entered.values()):
        raise RuleError('An empty stack cannot contain chips. Clear the quantities first.')
    if not explicit and not empty_stack:
        raise RuleError('Enter at least one quantity, or choose Empty stack.')
    total, breakdown = 0, []
    for row in values:
        quantity = entered.get(row['id'], 0)
        subtotal = row['value'] * quantity
        total += subtotal
        if total > MAX_AMOUNT:
            raise RuleError('That stack value is too large.')
        breakdown.append({**row, 'quantity': quantity, 'subtotal': subtotal})
    return total, breakdown
