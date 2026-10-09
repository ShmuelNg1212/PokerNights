"""Geometry for the charts on a player's page. The server works out every position; the template draws them.

Positions are percentages of the chart's box (0 at the left and the top), so the drawing stretches to
any width. They are floats because they place marks on a screen. The amounts beside them stay integers.
"""

from dataclasses import dataclass

from ledger import money

MOST = 60  # sessions drawn; a longer record shows its latest
FEWEST = 3
CLEAR = 9.0  # the least distance between two side labels
PAD = 8.0  # room above and below the line, so its stroke and end mark are never cut


@dataclass
class Point:
    """One session: where its running total sits on the line, and its own bar beneath."""

    x: float
    y: float
    total: int
    net: int
    up: bool
    bar_top: float
    bar_height: float
    date: object
    table: str
    night_id: int
    net_text: str
    total_text: str


@dataclass
class Chart:
    points: list
    path: str
    zero: float  # where the zero line crosses the running-profit chart
    bar_zero: float  # the baseline of the per-session bars
    labels: list  # (position, text) for the highest total, zero and the lowest
    first_label: str
    last_label: str
    end_label: str
    clipped: bool

    @property
    def end(self):
        return self.points[-1]


def _round(value: float) -> float:
    return round(value, 2)


def running_chart(record, unit):
    """The running total after each session as a line, and each session's result as a bar. None under three sessions."""
    if record.sessions < FEWEST:
        return None
    results, totals = record.results[-MOST:], record.running[-MOST:]
    count = len(results)
    high, low = max(0, *totals), min(0, *totals)
    span = (high - low) or 1

    def height(total):
        return _round(PAD + (high - total) * (100 - 2 * PAD) / span)

    most_up, most_down = max(0, *(r.net for r in results)), max(0, *(-r.net for r in results))
    reach = (most_up + most_down) or 1
    bar_zero = _round(most_up * 100 / reach) if most_up + most_down else 50.0
    points = []
    for index, (result, total) in enumerate(zip(results, totals)):
        size = _round(abs(result.net) * 100 / reach)
        top = _round(bar_zero - size) if result.net > 0 else bar_zero
        points.append(Point(
            x=_round((index + 0.5) * 100 / count), y=height(total), total=total, net=result.net, up=result.net > 0,
            bar_top=max(top, 0.0), bar_height=min(size, 100.0 - max(top, 0.0)), date=result.date, table=result.table,
            night_id=result.night_id, net_text=money.format_signed_amount(result.net, unit),
            total_text=money.format_signed_amount(total, unit),
        ))
    labels = [(height(value), money.format_signed_amount(value, unit)) for value in dict.fromkeys((high, 0, low))]
    # A zero line that sits on top of the highest or lowest label keeps its line and loses its words.
    labels = [(y, text) for y, text in labels if text != money.format_signed_amount(0, unit)
              or all(abs(y - other) >= CLEAR for other, _ in labels if other != y)]
    return Chart(
        points=points, path="M" + "L".join(f"{p.x:g} {p.y:g}" for p in points), zero=height(0), bar_zero=bar_zero,
        labels=labels, first_label=_day(results[0].date), last_label=_day(results[-1].date),
        end_label=points[-1].total_text, clipped=record.sessions > MOST,
    )


def _day(date) -> str:
    return f"{date:%b} {date.day}"
