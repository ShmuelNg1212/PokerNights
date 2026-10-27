"""Presentation only: tokens, icons and plain input amounts."""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from ledger.money import plain_amount

register = template.Library()

@register.filter(name="plain")
def plain(value, unit):
    return plain_amount(value, unit)

def token(participant, participants) -> tuple:
    """``(label, colour number)`` of a player's chip: an initial, or two letters when initials collide."""
    name = participant.member.display_name.strip()
    initial = name[:1].upper() or "?"
    peers = [p for p in participants if p.member.display_name.strip()[:1].upper() == initial]
    if len(peers) > 1:
        used = set()
        for peer in sorted(peers, key=lambda p: p.join_order):
            text = peer.member.display_name.strip().upper()
            words = text.split()
            label = words[0][:1] + words[-1][:1] if len(words) > 1 else text[:2]
            if label in used:
                label = next((text[:1] + char for char in text[2:] if text[:1] + char not in used), f"{text[:1]}{peer.join_order}")
            used.add(label)
            if peer is participant or (getattr(participant, "pk", None) is not None and peer.pk == participant.pk):
                initial = label
                break
    return initial, (participant.join_order - 1) % 10 + 1


@register.simple_tag
def player_token(participant, participants):
    initial, colour = token(participant, participants)
    # data-m names the player, so a screen change can carry the chip to the same player's row (turbo-setup.js).
    return format_html('<span class="chip k{}" data-m="{}" aria-hidden="true">{}</span>', colour, getattr(participant.member, "pk", ""), initial)

@register.simple_tag
def member_token(member, members):
    from types import SimpleNamespace
    peers = [SimpleNamespace(member=m, join_order=m.pk, pk=m.pk) for m in members]
    return player_token(next(p for p in peers if p.pk == member.pk), peers)


@register.simple_tag
def account_token(user):
    """The signed-in person's chip in the header: the username's first letter, a colour that stays with the account."""
    initial = user.get_username().strip()[:1].upper() or "?"
    return format_html('<span class="chip account-chip k{}" aria-hidden="true">{}</span>', (user.pk - 1) % 10 + 1, initial)


@register.simple_tag
def buy_in_stack(count):
    edges = '<i></i>' * min(count, 5)
    extra = f'<span>+{count - 5}</span>' if count > 5 else ''
    return format_html('<span class="buy-stack" aria-hidden="true">{}{}</span>', mark_safe(edges), mark_safe(extra))

@register.simple_tag
def double_default(settings, unit):
    return plain_amount(min(settings.default_buy_in * 2, settings.max_buy_in), unit)

# Lucide SVG paths, ISC licensed; see static/icons/LICENSE.
ICONS = {'settings': '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />\n  <circle cx="12" cy="12" r="3" />', 'chevron-right': '<path d="m9 18 6-6-6-6" />', 'chevron-down': '<path d="m6 9 6 6 6-6" />', 'plus': '<path d="M5 12h14" />\n  <path d="M12 5v14" />', 'arrow-left': '<path d="m12 19-7-7 7-7" />\n  <path d="M19 12H5" />', 'arrow-right': '<path d="M5 12h14" />\n  <path d="m12 5 7 7-7 7" />', 'arrow-up-right': '<path d="M7 7h10v10" />\n  <path d="M7 17 17 7" />', 'arrow-down-right': '<path d="m7 7 10 10" />\n  <path d="M17 7v10H7" />', 'minus': '<path d="M5 12h14" />', 'x': '<path d="M18 6 6 18" />\n  <path d="m6 6 12 12" />', 'check': '<path d="M20 6 9 17l-5-5" />', 'ellipsis': '<circle cx="12" cy="12" r="1" />\n  <circle cx="19" cy="12" r="1" />\n  <circle cx="5" cy="12" r="1" />', 'log-out': '<path d="m16 17 5-5-5-5" />\n  <path d="M21 12H9" />\n  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />'}

@register.simple_tag
def icon(name):
    return format_html('<svg class="icon icon-{}" viewBox="0 0 24 24" aria-hidden="true">{}</svg>', name, mark_safe(ICONS.get(name, '')))

@register.filter
def display_amount(value, unit):
    from ledger.money import format_amount
    text = format_amount(value, unit)
    if unit == "chips":
        number, word = text.rsplit(" ", 1)
        return format_html('{} <small>{}</small>', number, word)
    return text


ICONS.update({
    'user': '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />\n  <circle cx="12" cy="7" r="4" />',
    'arrow-up': '<path d="m5 12 7-7 7 7" />\n  <path d="M12 19V5" />',
    'arrow-down': '<path d="M12 5v14" />\n  <path d="m19 12-7 7-7-7" />',
    # Table alerts in the header (2026-10-16): off, on (the same bell, filled) and blocked.
    'bell': '<path d="M10.268 21a2 2 0 0 0 3.464 0" />\n  <path d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326" />',
    'bell-filled': '<path d="M10.268 21a2 2 0 0 0 3.464 0" />\n  <path fill="currentColor" d="M3.262 15.326A1 1 0 0 0 4 17h16a1 1 0 0 0 .74-1.673C19.41 13.956 18 12.499 18 8A6 6 0 0 0 6 8c0 4.499-1.411 5.956-2.738 7.326" />',
    'bell-off': '<path d="M10.268 21a2 2 0 0 0 3.464 0" />\n  <path d="M17 17H4a1 1 0 0 1-.74-1.673C4.59 13.956 6 12.499 6 8a6 6 0 0 1 .258-1.742" />\n  <path d="m2 2 20 20" />\n  <path d="M8.668 3.01A6 6 0 0 1 18 8c0 2.687.77 4.653 1.707 6.05" />',
})


@register.filter
def state_word(state):
    """A set's state in the words the screens use. The stored names are 'setup' and 'running'."""
    from games.models import GameSession
    return GameSession.STATE_WORDS.get(state, state)


@register.simple_tag
def own_count(line):
    """Where a player's own count is, for the "Your count" card: the stage, the amount it names and each step's state.

    Counted (the player entered it, or the host counted for them), confirmed by the host, cashed out.
    """
    if line.status == "awaiting":
        stage, amount = ("sent", line.entered.amount) if line.entered else ("open", "")
    elif line.status == "ready":
        stage, amount = "confirmed", line.count.amount
    else:
        stage, amount = "cashed", line.cashed_out
    reached = ["open", "sent", "confirmed", "cashed"].index(stage)  # how many steps are finished
    steps = [
        {"name": name, "state": "done" if number < reached else "now" if number == reached else "todo",
         "fresh": number == reached - 1,
         # The player's own turn is the field; every later step waits for the host.
         "waits": number == reached and reached > 0}
        for number, name in enumerate(["Counted", "Confirmed", "Cashed out"])
    ]
    words = ["Step 1 of 3: send your count.", "Step 2 of 3: counted, waiting for the host to confirm.",
             "Step 3 of 3: confirmed, waiting for the host to cash you out.", "All 3 steps done: cashed out."][reached]
    return {"stage": stage, "amount": amount, "steps": steps, "words": words}


@register.filter
def focus_unless(field, card):
    """The field's input, without its autofocus while the chat-browser card leads the page.

    Focus scrolls a short phone past the card. A refused form keeps the focus on the refused field.
    """
    if card and not field.form.errors:
        return field.as_widget(attrs={"autofocus": False})
    return field.as_widget()


@register.filter
def ordinal_place(number):
    """1st, 2nd, 3rd, 4th … for a place in line."""
    number = int(number)
    suffix = "th" if 10 <= number % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"
