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
    return format_html('<span class="chip k{}" aria-hidden="true">{}</span>', colour, initial)

@register.simple_tag
def buy_in_stack(count):
    edges = '<i></i>' * min(count, 5)
    extra = f'<span>+{count - 5}</span>' if count > 5 else ''
    return format_html('<span class="buy-stack" aria-hidden="true">{}{}</span>', mark_safe(edges), mark_safe(extra))

@register.simple_tag
def play_percent(summary):
    return min(100, max(0, summary.in_play * 100 // summary.total)) if summary.total else 0

@register.simple_tag
def double_default(settings, unit):
    return plain_amount(min(settings.default_buy_in * 2, settings.max_buy_in), unit)

# Lucide SVG paths, ISC licensed; see static/icons/LICENSE.
ICONS = {'plus': '<path d="M5 12h14" />\n  <path d="M12 5v14" />', 'arrow-left': '<path d="m12 19-7-7 7-7" />\n  <path d="M19 12H5" />', 'arrow-up-right': '<path d="M7 7h10v10" />\n  <path d="M7 17 17 7" />', 'arrow-down-right': '<path d="m7 7 10 10" />\n  <path d="M17 7v10H7" />', 'minus': '<path d="M5 12h14" />', 'x': '<path d="M18 6 6 18" />\n  <path d="m6 6 12 12" />', 'check': '<path d="M20 6 9 17l-5-5" />', 'ellipsis': '<circle cx="12" cy="12" r="1" />\n  <circle cx="19" cy="12" r="1" />\n  <circle cx="5" cy="12" r="1" />', 'log-out': '<path d="m16 17 5-5-5-5" />\n  <path d="M21 12H9" />\n  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />'}

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
