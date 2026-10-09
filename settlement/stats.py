"""Player statistics, worked out when read from the frozen results of closed sessions. Nothing is stored.

One query fetches a group's counted results for one unit. Every figure, period, rank and
movement is then plain arithmetic over that list, in integers: amounts are never floats,
and a division rounds toward zero so that a loss is never shown larger than it is.
"""

import calendar
import datetime
from dataclasses import dataclass, field

from groups.models import Member

from .queries import counted_results


def toward_zero(value: int, by: int) -> int:
    """``value / by`` as an integer, rounded toward zero."""
    whole = abs(value) // by
    return whole if value >= 0 else -whole


@dataclass(frozen=True)
class SessionResult:
    """One player's result in one closed session, its sets added together."""

    member_id: int
    night_id: int
    date: datetime.date
    table: str
    net: int
    bought_in: int
    rebuys: int  # buy-ins beyond the first in each set
    rake: int
    seconds: int | None  # time at the table; None when a set was played before time was recorded


def fetch(group, unit) -> list:
    """Every counted result of the group in one unit, as one row per player and session, oldest first."""
    rows = counted_results().filter(group=group, unit=unit).values_list(
        "member_id", "finalization__session__night_id", "finalization__session__night__game_date",
        "finalization__session__night__table__name", "net", "buy_in_total", "buy_in_count", "rake_total", "play_seconds",
    )
    found = {}
    for member_id, night_id, date, table, net, bought_in, count, rake, seconds in rows:
        key = (member_id, night_id)
        rebuys = max(count - 1, 0)
        if key not in found:
            found[key] = [member_id, night_id, date, table, net, bought_in, rebuys, rake, seconds]
            continue
        row = found[key]
        row[4] += net
        row[5] += bought_in
        row[6] += rebuys
        row[7] += rake
        row[8] = None if row[8] is None or seconds is None else row[8] + seconds
    return sorted((SessionResult(*row) for row in found.values()), key=lambda r: (r.date, r.night_id, r.member_id))


def members_of(rows) -> dict:
    """``{member id: Member}`` for the players in ``rows``, whatever their status in the group."""
    return Member.objects.in_bulk({row.member_id for row in rows})


def _add_months(first: datetime.date, months: int) -> datetime.date:
    index = first.year * 12 + first.month - 1 + months
    return datetime.date(index // 12, index % 12 + 1, 1)


def _month_end(first: datetime.date) -> datetime.date:
    return first.replace(day=calendar.monthrange(first.year, first.month)[1])


@dataclass(frozen=True)
class Period:
    """A span of session dates. ``start`` and ``end`` are inclusive; None is open."""

    slug: str
    kind: str  # all, year, recent, month
    label: str
    start: datetime.date | None = None
    end: datetime.date | None = None

    # Sessions a player needs in the period to hold a place on the board.
    MINIMUMS = {"all": 3, "year": 3, "recent": 2, "month": 1}

    @classmethod
    def all_time(cls, end=None):
        return cls("all", "all", "All time", None, end)

    @classmethod
    def year(cls, year: int, label="This year"):
        return cls("year", "year", label, datetime.date(year, 1, 1), datetime.date(year, 12, 31))

    @classmethod
    def recent(cls, last_month: datetime.date):
        """Three calendar months ending with the month of ``last_month``."""
        last = last_month.replace(day=1)
        return cls("recent", "recent", "Last 3 months", _add_months(last, -2), _month_end(last))

    @classmethod
    def month(cls, first: datetime.date):
        first = first.replace(day=1)
        return cls(f"{first:%Y-%m}", "month", f"{first:%B %Y}", first, _month_end(first))

    @classmethod
    def parse(cls, slug, today: datetime.date):
        """The period a page asked for; anything unknown is all time."""
        if slug == "year":
            return cls.year(today.year)
        if slug == "recent":
            return cls.recent(today)
        try:
            return cls.month(datetime.datetime.strptime(slug or "", "%Y-%m").date())
        except ValueError:
            return cls.all_time()

    @property
    def minimum(self) -> int:
        return self.MINIMUMS[self.kind]

    def contains(self, date: datetime.date) -> bool:
        return (self.start is None or date >= self.start) and (self.end is None or date <= self.end)

    def previous(self, rows):
        """The period a board is compared with: the one before, or all time before the latest session."""
        if self.kind == "year":
            return Period.year(self.start.year - 1, "Last year")
        if self.kind == "recent":
            return Period.recent(_add_months(self.start, -1))
        if self.kind == "month":
            return Period.month(_add_months(self.start, -1))
        dates = [row.date for row in rows if self.contains(row.date)]
        return Period.all_time(max(dates) - datetime.timedelta(days=1)) if dates else None


@dataclass
class PlayerRecord:
    """One player's sessions in a period, oldest first, and what they add up to."""

    member: object
    results: list = field(default_factory=list)

    @property
    def pk(self):
        return self.member.pk

    @property
    def sessions(self) -> int:
        return len(self.results)

    @property
    def net(self) -> int:
        return sum(r.net for r in self.results)

    @property
    def wins(self) -> int:
        return sum(1 for r in self.results if r.net > 0)

    @property
    def win_percent(self) -> int:
        return self.wins * 100 // self.sessions if self.sessions else 0

    @property
    def average(self) -> int:
        return toward_zero(self.net, self.sessions) if self.sessions else 0

    @property
    def bought_in(self) -> int:
        return sum(r.bought_in for r in self.results)

    @property
    def return_percent(self):
        """Profit or loss as a whole percent of the money bought in, or None when nothing was."""
        return toward_zero(self.net * 100, self.bought_in) if self.bought_in else None

    @property
    def _timed(self) -> list:
        return [r for r in self.results if r.seconds]

    @property
    def timed_sessions(self) -> int:
        return len(self._timed)

    @property
    def seconds(self) -> int:
        return sum(r.seconds for r in self._timed)

    @property
    def per_hour(self):
        """Profit or loss per hour at the table over the sessions with recorded time, or None when none have."""
        timed = self._timed
        return toward_zero(sum(r.net for r in timed) * 3600, self.seconds) if timed else None

    @property
    def rebuys(self) -> int:
        return sum(r.rebuys for r in self.results)

    @property
    def rebuys_per_session(self) -> str:
        tenths = self.rebuys * 10 // self.sessions if self.sessions else 0
        return f"{tenths // 10}.{tenths % 10}"

    @property
    def rake(self) -> int:
        return sum(r.rake for r in self.results)

    @property
    def running(self) -> list:
        """The running total after each session."""
        total, out = 0, []
        for r in self.results:
            total += r.net
            out.append(total)
        return out

    @property
    def best(self):
        return max(self.results, key=lambda r: r.net, default=None)  # the earliest on a tie

    @property
    def worst(self):
        return min(self.results, key=lambda r: r.net, default=None)

    @property
    def last(self):
        return self.results[-1] if self.results else None

    @property
    def first(self):
        return self.results[0] if self.results else None

    @property
    def current_run(self):
        """``("won" | "lost", sessions in a row)`` ending with the latest session, or None. Break-even ends a run."""
        if not self.results or not self.results[-1].net:
            return None
        won = self.results[-1].net > 0
        length = 0
        for r in reversed(self.results):
            if not r.net or (r.net > 0) != won:
                break
            length += 1
        return ("won" if won else "lost", length)

    @property
    def longest_win_run(self) -> int:
        best = run = 0
        for r in self.results:
            run = run + 1 if r.net > 0 else 0
            best = max(best, run)
        return best


# What a board can be ordered by: the figure, highest first. None sorts as "no figure".
SORTS = {
    "profit": lambda record: record.net,
    "average": lambda record: record.average,
    "return": lambda record: record.return_percent,
    "hour": lambda record: record.per_hour,
    "sessions": lambda record: record.sessions,
}


@dataclass
class BoardLine:
    record: PlayerRecord
    place: int | None = None  # None: not ranked
    move: object = None  # places gained (+) or lost (−) since the earlier board, "new", or None


@dataclass
class Board:
    period: Period
    sort: str
    ranked: list
    unranked: list
    has_time: bool  # some session in the period has recorded time, so "per hour" means something

    @property
    def minimum(self) -> int:
        return self.period.minimum

    @property
    def ranked_count(self) -> int:
        return len(self.ranked)

    def line(self, member_id):
        return next((line for line in self.ranked + self.unranked if line.record.pk == member_id), None)


def records(rows, members, period) -> dict:
    """``{member id: PlayerRecord}`` for the sessions of ``rows`` that fall in ``period``."""
    found = {}
    for row in rows:
        if period.contains(row.date) and row.member_id in members:
            found.setdefault(row.member_id, PlayerRecord(members[row.member_id])).results.append(row)
    return found


def _ranked(found, period, sort) -> tuple:
    figure = SORTS[sort]

    def order(record):
        return (-figure(record), record.member.display_name.lower(), record.pk)

    ranked = [r for r in found.values() if r.sessions >= period.minimum and figure(r) is not None]
    places = {r.pk for r in ranked}
    rest = [r for r in found.values() if r.pk not in places]
    return sorted(ranked, key=order), sorted(rest, key=lambda r: (-r.net, r.member.display_name.lower(), r.pk))


def board(rows, members, period, sort="profit") -> Board:
    """Players in order for one period, those under its minimum apart, and each ranked player's movement."""
    found = records(rows, members, period)
    has_time = any(r.timed_sessions for r in found.values())
    if sort not in SORTS or (sort == "hour" and not has_time):
        sort = "profit"
    ranked, rest = _ranked(found, period, sort)
    earlier = period.previous(rows)
    before = [r.pk for r in _ranked(records(rows, members, earlier), earlier, sort)[0]] if earlier else []
    lines = []
    for place, record in enumerate(ranked, 1):
        move = None
        if before:
            move = before.index(record.pk) + 1 - place if record.pk in before else "new"
        lines.append(BoardLine(record, place, move or None))
    return Board(period, sort, lines, [BoardLine(record) for record in rest], has_time)
