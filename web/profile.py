"""What a person's profile shows: their record across every group, and their own settings. Read-only.

Pesos add up across groups. Chips never do: a chip is worth something different in each group,
so each chips group is its own line with its own figure.
"""

from dataclasses import dataclass, replace
from urllib.parse import urlencode

from django.urls import reverse
from django.utils import timezone

from accounts.forms import ChangePasswordForm
from accounts.views import PASSWORD_ERRORS
from groups.forms import NameForm
from groups.http import take_form
from groups.models import Member
from groups.views import PROFILE_NAME
from ledger import money
from settlement import stats
from settlement.stats import Period, PlayerRecord

from . import charts
from .stats import Figure, Tile, signed, where

@dataclass
class GroupLine:
    """One group's part of the record. ``url`` is empty where the person is no longer a member."""

    name: str
    record: PlayerRecord
    figure: Figure
    url: str
    left: bool


def periods(today) -> list:
    return [Period.all_time(), Period.parse("year", today)]


def choose_period(slug, today) -> Period:
    """All time or this year; anything else is all time."""
    return Period.parse("year", today) if slug == "year" else Period.all_time()


def group_lines(rows, unit, period, members) -> list:
    """One line per group, largest profit first, then by name."""
    by_group = {}
    for row in rows:
        by_group.setdefault(row.group_id, []).append(row)
    lines = []
    for group_id, results in by_group.items():
        record = PlayerRecord(None, results)
        member = members.get(group_id)
        active = member is not None and member.status == Member.Status.ACTIVE
        url = ""
        if active:
            url = reverse("player", args=[group_id, member.pk]) + "?" + urlencode({"period": period.slug, "unit": unit})
        figure = Figure("Even", 0) if record.net == 0 else Figure(signed(record.net, unit), record.net)
        lines.append(GroupLine(results[0].group, record, figure, url, not active))
    return sorted(lines, key=lambda line: (-line.record.net, line.name.lower()))


def night_of(result, today) -> str:
    """"Sunday Game · Aug 23", with the year when it is not this one."""
    day = f"{result.date:%b} {result.date.day}" + (f", {result.date.year}" if result.date.year != today.year else "")
    return f"{result.group} · {day}"


def headline(record, unit) -> list:
    """Four tiles: the count of sessions is in the line under the total."""
    best, worst, today = record.best, record.worst, timezone.localdate()
    return [
        Tile("Win rate", f"{record.win_percent}%", note=f"{record.wins} of {record.sessions}"),
        Tile("Average per session", signed(record.average, unit), record.average),
        Tile("Best night", signed(best.net, unit), best.net, note=night_of(best, today)),
        Tile("Worst night", signed(worst.net, unit), worst.net, note=night_of(worst, today)),
    ]


def own_name(members) -> tuple:
    """``(name, names by group)``: the one name used in every group, or "" and each group's name when they differ."""
    active = [m for m in members.values() if m.status == Member.Status.ACTIVE]
    names = {m.display_name for m in active}
    by_group = sorted(((m.group.name, m.display_name) for m in active), key=lambda pair: pair[0].lower())
    return (names.pop() if len(names) == 1 else ""), by_group


def password_form(request, user):
    """The password form, with the errors of a refused change but never the passwords typed."""
    errors = request.session.pop(PASSWORD_ERRORS, None)
    if not errors:
        return ChangePasswordForm(user)
    form = ChangePasswordForm(user, data={})
    form.is_valid()
    form._errors.clear()
    for name, words in errors.items():
        for words_one in words:
            form.add_error(None if name == "__all__" else name, words_one)
    return form


def profile_context(request, user) -> dict:
    today = timezone.localdate()
    period = choose_period(request.GET.get("period"), today)
    units = stats.units_for_user(user)
    members = {
        m.group_id: m
        for m in Member.objects.filter(user=user, group__archived_at__isnull=True).select_related("group")
    }
    pesos = [r for r in stats.fetch_for_user(user, money.PHP) if period.contains(r.date)] if money.PHP in units else []
    chips = [r for r in stats.fetch_for_user(user, money.CHIPS) if period.contains(r.date)] if money.CHIPS in units else []
    record = PlayerRecord(None, pesos)
    # The chart's readout names the group, which says more here than the table's name.
    chart_record = PlayerRecord(None, [replace(r, table=r.group) for r in pesos])
    name, names = own_name(members)
    return {
        "stat_period": period,
        "stat_periods": periods(today),
        "stat_where": where(period),
        "has_any": bool(units),
        "record": record,
        "net": Figure(signed(record.net, money.PHP), record.net),
        "chart": charts.running_chart(chart_record, money.PHP) if pesos else None,
        "tiles": headline(record, money.PHP) if pesos else [],
        "pesos_groups": group_lines(pesos, money.PHP, period, members),
        "chips_groups": group_lines(chips, money.CHIPS, period, members),
        "own_name": name,
        "names_by_group": names,
        "in_a_group": bool(names),
        "name_form": take_form(request, PROFILE_NAME, NameForm, initial={"name": name}),
        "password_form": password_form(request, user),
    }
