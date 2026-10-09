"""What the Stats tab and a player's page show. Read-only: every figure comes from ``settlement.stats``."""

from dataclasses import dataclass
from urllib.parse import urlencode

from django.urls import reverse
from django.utils import timezone

from games import clock
from ledger import money
from settlement import stats
from settlement.stats import Period

from . import charts

SORT_LABELS = [("profit", "Profit"), ("average", "Average"), ("return", "Return"), ("hour", "Per hour"), ("sessions", "Sessions")]
SHOWN = 10  # sessions listed on a player's page before "Show all"


def ordinal(place: int) -> str:
    if 10 <= place % 100 <= 20:
        return f"{place}th"
    return f"{place}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(place % 10, 'th') }"


def percent(value) -> str:
    """``+28%``, ``−33%``, ``0%``, or a dash when there is no figure."""
    if value is None:
        return "—"
    return f"+{value}%" if value > 0 else f"{money.MINUS}{-value}%" if value < 0 else "0%"


def signed(value, unit, suffix="") -> str:
    return "—" if value is None else money.format_signed_amount(value, unit) + suffix


@dataclass
class Figure:
    """A figure as shown: its words, and the number that decides the up or down mark (None: no mark)."""

    text: str
    sign: object = None


def figure(record, sort, unit) -> Figure:
    if sort == "average":
        return Figure(signed(record.average, unit), record.average)
    if sort == "return":
        return Figure(percent(record.return_percent), record.return_percent)
    if sort == "hour":
        return Figure(signed(record.per_hour, unit, " / h"), record.per_hour)
    if sort == "sessions":
        return Figure(str(record.sessions))
    return Figure(signed(record.net, unit), record.net)


def choose_unit(request, periods) -> str:
    unit = request.GET.get("unit")
    if unit not in periods:
        unit = money.PHP if money.PHP in periods or not periods else next(iter(periods))
    return unit


def rank_text(line, board) -> str:
    if line is None:
        return ""
    if line.place is None:
        return f"Not ranked yet: {line.record.sessions} of {board.minimum} session{'' if board.minimum == 1 else 's'}"
    return f"{ordinal(line.place)} of {board.ranked_count}"


def _query(**params) -> str:
    return urlencode(sorted(params.items()))


def board_context(request, me, periods) -> dict:
    """The viewer's summary and the board for one unit, period and order."""
    unit = choose_unit(request, periods)
    rows = stats.fetch(me.group, unit) if periods else []
    members = stats.members_of(rows)
    period = Period.parse(request.GET.get("period") or request.GET.get("month"), timezone.localdate())
    board = stats.board(rows, members, period, request.GET.get("sort", "profit"))
    keep = _query(period=period.slug, unit=unit)
    for line in board.ranked + board.unranked:
        line.figure = figure(line.record, board.sort, unit)
        line.profit = None if board.sort == "profit" else Figure(signed(line.record.net, unit), line.record.net)
        line.url = reverse("player", args=[me.group_id, line.record.pk]) + "?" + keep
        line.left = line.record.member.status != "active"
        line.move_dir = "new" if line.move == "new" else "up" if (line.move or 0) > 0 else "down" if line.move else ""
        line.move_text = "New" if line.move == "new" else f"{'up' if (line.move or 0) > 0 else 'down'} {abs(line.move)}" if line.move else ""
        line.move_count = abs(line.move) if isinstance(line.move, int) else None
    mine = board.line(me.pk)
    return {
        "stat_unit": unit,
        "stat_units": [u for u in (money.PHP, money.CHIPS) if u in periods],
        "stat_period": period,
        "stat_periods": [Period.all_time(), Period.parse("year", timezone.localdate()), Period.parse("recent", timezone.localdate())],
        "stat_months": [(f"{m:%Y-%m}", f"{m:%B %Y}") for m in periods.get(unit, [])],
        "stat_sort": board.sort,
        "stat_sorts": [(slug, label) for slug, label in SORT_LABELS if slug != "hour" or board.has_time],
        "stat_board": board,
        "stat_ranked": board.ranked,
        "stat_unranked": board.unranked,
        "stat_members": [line.record.member for line in board.ranked + board.unranked],
        "stat_mine": mine,
        "stat_mine_rank": rank_text(mine, board),
        "stat_mine_last": Figure(signed(mine.record.last.net, unit), mine.record.last.net) if mine else None,
        "stat_where": where(period),
        "stat_keep": keep,
        "stats_pages": True,
    }


@dataclass
class SessionLine:
    result: object
    figure: Figure


def where(period) -> str:
    """The period inside a sentence: "this year", "in October 2026"."""
    return {"all": "yet", "year": "this year", "recent": "in the last 3 months"}.get(period.kind, f"in {period.label}")


@dataclass
class Tile:
    label: str
    text: str
    sign: object = None
    note: str = ""


def tiles(record, unit) -> list:
    timed = record.timed_sessions
    hour_note = "" if timed in (0, record.sessions) else f"over {timed} of {record.sessions} sessions"
    return [
        Tile("Average per session", signed(record.average, unit), record.average),
        Tile("Return on buy-ins", percent(record.return_percent), record.return_percent),
        Tile("Per hour", signed(record.per_hour, unit), record.per_hour, hour_note or ("" if timed else "no time recorded")),
        Tile("Win rate", f"{record.win_percent}%", note=f"{record.wins} of {record.sessions}"),
        Tile("Rebuys per session", record.rebuys_per_session),
        Tile("Total bought in", money.format_amount(record.bought_in, unit)),
        Tile("Rake paid", money.format_amount(record.rake, unit)),
        Tile("Time at the table", clock.format_duration(record.seconds) if timed else "—", note=hour_note),
    ]


def run_text(run) -> str:
    if run is None:
        return "No run"
    return f"{'Won' if run[0] == 'won' else 'Lost'} {run[1]} in a row"


def player_context(request, me, member, periods) -> dict:
    """One player's record in the group for one unit and period, with their place on the profit board."""
    unit = choose_unit(request, periods)
    rows = stats.fetch(me.group, unit) if periods else []
    members = stats.members_of(rows)
    members.setdefault(member.pk, member)
    today = timezone.localdate()
    period = Period.parse(request.GET.get("period"), today)
    board = stats.board(rows, members, period, "profit")
    line = board.line(member.pk)
    record = line.record if line else stats.PlayerRecord(member)
    ever = stats.records(rows, members, Period.all_time()).get(member.pk)
    listed = list(reversed(record.results))
    show_all = request.GET.get("all") == "1"
    listed = [SessionLine(result, Figure(signed(result.net, unit), result.net)) for result in listed]
    keep = {"period": period.slug, "unit": unit}
    return {
        "member": member,
        "left": member.status != "active",
        "unit": unit,
        "stat_unit": unit,
        "stat_units": [u for u in (money.PHP, money.CHIPS) if u in periods],
        "stat_period": period,
        "stat_periods": [Period.all_time(), Period.parse("year", today), Period.parse("recent", today)],
        "stat_months": [(f"{m:%Y-%m}", f"{m:%B %Y}") for m in periods.get(unit, [])],
        "record": record,
        "net": Figure(signed(record.net, unit), record.net),
        "rank": rank_text(line, board),
        "since": f"{ever.sessions} session{'' if ever.sessions == 1 else 's'} since {ever.first.date:%b %Y}" if ever else "",
        "chart": charts.running_chart(record, unit),
        "tiles": tiles(record, unit) if record.sessions else [],
        "best": record.best,
        "worst": record.worst,
        "run": run_text(record.current_run),
        "longest": record.longest_win_run,
        "sessions": listed if show_all else listed[:SHOWN],
        "session_count": len(listed),
        "more": len(listed) > SHOWN and not show_all,
        "all_url": "?" + _query(all="1", **keep),
        "back_url": reverse("group", args=[me.group_id]) + "?" + _query(view="stats", sort=request.GET.get("sort", "profit"), **keep),
        "keep": _query(**keep),
        "members_one": [member],
        "stat_where": where(period),
        "is_me": member.pk == me.pk,
        "best_figure": Figure(signed(record.best.net, unit), record.best.net) if record.best else None,
        "worst_figure": Figure(signed(record.worst.net, unit), record.worst.net) if record.worst else None,
    }
