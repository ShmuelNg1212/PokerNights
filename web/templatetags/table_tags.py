"""Presentation only: tokens, icons and plain input amounts."""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from ledger.money import plain_amount

register = template.Library()

@register.filter(name="plain")
def plain(value, unit):
    return plain_amount(value, unit)

@register.simple_tag
def player_token(participant, participants):
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
    colour = (participant.join_order - 1) % 10 + 1
    # data-m names the player, so a screen change can carry the chip to the same player's row (turbo-setup.js).
    return format_html('<span class="chip k{}" data-m="{}" aria-hidden="true">{}</span>', colour, getattr(participant.member, "pk", ""), initial)

@register.simple_tag
def member_token(member, members):
    from types import SimpleNamespace
    peers = [SimpleNamespace(member=m, join_order=m.pk, pk=m.pk) for m in members]
    return player_token(next(p for p in peers if p.pk == member.pk), peers)


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
    return format_html('<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">{}</svg>', mark_safe(ICONS.get(name, '')))

@register.filter
def display_amount(value, unit):
    from ledger.money import format_amount
    text = format_amount(value, unit)
    if unit == "chips":
        number, word = text.rsplit(" ", 1)
        return format_html('{} <small>{}</small>', number, word)
    return text


ICONS.update({
    'arrow-up': '<path d="m5 12 7-7 7 7" />\n  <path d="M12 19V5" />',
    'arrow-down': '<path d="M12 5v14" />\n  <path d="m19 12-7 7-7-7" />',
})


STATE_WORDS = {"setup": "Draft", "open": "Open", "running": "In play", "reconciliation": "Counting up", "finalized": "Final", "canceled": "Canceled"}


@register.filter
def state_word(state):
    """A set's state in the words the screens use. The stored names are 'setup' and 'running'."""
    return STATE_WORDS.get(state, state)
