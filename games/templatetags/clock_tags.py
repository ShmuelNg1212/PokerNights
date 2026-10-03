from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from games import clock

register = template.Library()


@register.filter
def duration(seconds):
    """Seconds → ``1 h 05 min``. ``None`` → ``not recorded``."""
    return clock.format_duration(seconds)


@register.simple_tag
def clock_value(seconds, running=False):
    """A duration that a small script keeps moving while it runs. The server's figure is the truth."""
    if seconds is None:
        return "not recorded"
    return format_html(
        '<span data-clock data-seconds="{}"{}>{}</span>',
        seconds, mark_safe(" data-running") if running else "", clock.format_duration(seconds),
    )
