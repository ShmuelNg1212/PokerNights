"""Reading a set's seat draw: who sits where, and what each seat is called on the first hand.

Nothing here writes. The draw itself is made in ``services.draw_seats``.
"""

import math
from dataclasses import dataclass, field

from django.utils import timezone

from .models import GameSession, Participant, SeatPlace

# How long after a draw, or after the dealer chose, a phone still plays it by itself (seats.js),
# and how long the set page asks the server more often while a draw waits for a seat.
FRESH_SECONDS = 120


def positions(count: int) -> list:
    """``(name, short)`` for each seat clockwise from the dealer, on the first hand."""
    if count < 2:
        return [("Dealer", "D")][:count]
    if count == 2:
        return [("Dealer and small blind", "D"), ("Big blind", "BB")]
    names = [("Dealer", "D"), ("Small blind", "SB"), ("Big blind", "BB")]
    rest = count - 3
    late = [("Hijack", "HJ"), ("Cutoff", "CO")][-min(rest - 1, 2):] if rest > 1 else []
    middle = rest - 1 - len(late)
    early = [("Under the gun", "UTG")] if rest else []
    between = [("Middle", "MP")] if middle == 1 else [(f"Middle {number}", f"MP{number}") for number in range(1, middle + 1)]
    return names + early + between + late


# The drawn table is a racetrack: straight sides and round ends. The same rule is written in
# static/js/seats.js (edge), which places the players on the stage; the two must agree.
WIDE = 1.25      # the still table on the set page is five wide and four tall
MARGIN = 0.07    # how far inside the table's box the seats sit, as a share of its shorter side


def edge(index: int, count: int, width: float, height: float) -> tuple:
    """Where seat ``index`` of ``count`` sits on a table drawn in a ``width`` by ``height`` box.

    ``(x, y, turn)``: x and y from the box's centre, and the way the seat faces outward in
    degrees clockwise from straight up. Seat 0 is top centre; the rest follow clockwise, each
    the same distance from the next along the edge, so none bunch up on the round ends.
    """
    margin = MARGIN * min(width, height)
    a, b = width / 2 - margin, height / 2 - margin
    r = min(a, b)
    lx, ly = a - r, b - r  # half of each straight: along the top and bottom, and along the sides
    quarter = math.pi * r / 2
    # Clockwise from top centre: (length, kind, where it starts or its centre, the turn it starts with).
    pieces = [
        (lx, "line", (0, -b), (1, 0), 0), (quarter, "arc", (lx, -ly), None, 0),
        (2 * ly, "line", (a, -ly), (0, 1), 90), (quarter, "arc", (lx, ly), None, 90),
        (2 * lx, "line", (lx, b), (-1, 0), 180), (quarter, "arc", (-lx, ly), None, 180),
        (2 * ly, "line", (-a, ly), (0, -1), 270), (quarter, "arc", (-lx, -ly), None, 270),
        (lx, "line", (-lx, -b), (1, 0), 0),
    ]
    left = sum(length for length, *_ in pieces) * (index % count) / count
    for length, kind, origin, along, turn in pieces:
        if left > length:
            left -= length
            continue
        if kind == "line":
            return origin[0] + along[0] * left, origin[1] + along[1] * left, float(turn)
        swept = left / r  # radians along the corner
        angle = math.radians(turn - 90) + swept
        return origin[0] + r * math.cos(angle), origin[1] + r * math.sin(angle), turn + math.degrees(swept)
    return 0.0, -b, 0.0


def spot(index: int, count: int, wide: float = WIDE) -> tuple:
    """Seat ``index`` on the still table, as ``(left %, top %, turn in degrees)``."""
    x, y, turn = edge(index, count, wide, 1.0)
    return round(50 + 100 * x / wide, 2), round(50 + 100 * y, 2), round(turn, 1)


@dataclass
class Seat:
    participant: Participant
    distance: int            # places clockwise from the dealer
    index: int | None        # the seat on the drawn table; None until the dealer has chosen
    position: tuple | None   # (name, short) on the first hand; None for a player seated late
    late: bool = False
    count: int = 0
    ring: int = 0            # the place in the ring of players before the draw: the order of joining

    @property
    def is_dealer(self):
        return self.distance == 0

    @property
    def away(self):
        return self.participant.status == Participant.Status.LEFT

    @property
    def number(self):
        return None if self.index is None else self.index + 1

    @property
    def xy(self):
        return None if self.index is None else spot(self.index, self.count)


@dataclass
class Seating:
    draw: object
    seats: list = field(default_factory=list)       # clockwise from the dealer
    unseated: list = field(default_factory=list)    # at the table, without a place in the draw
    fresh: bool = False

    @property
    def stale(self):
        return self.draw.stale

    @property
    def chosen(self):
        return self.draw.dealer_seat is not None

    @property
    def state(self):
        return "stale" if self.stale else ("seated" if self.chosen else "choosing")

    @property
    def dealer(self):
        return next((seat.participant for seat in self.seats if seat.is_dealer), None)

    @property
    def count(self):
        return len(self.seats)

    @property
    def by_seat(self):
        """The seats in the order of the drawn table, top seat first."""
        return sorted(self.seats, key=lambda seat: seat.index if seat.index is not None else seat.distance)

    @property
    def spots(self):
        """Every seat of the drawn table as ``(index, number, x, y, turn)``, for the empty table."""
        return [(index, index + 1, *spot(index, self.count)) for index in range(self.count)]

    @property
    def poll_fast(self):
        return self.state == "choosing" and self.fresh


def seating(session: GameSession, participants=None) -> Seating | None:
    """The set's current draw as seats, or None when there is none. One query."""
    places = list(
        SeatPlace.objects.filter(draw__session=session, draw__is_current=True).select_related("draw").order_by("rank")
    )
    if not places:
        return None
    draw = places[0].draw
    if participants is None:
        participants = list(session.participants.select_related("member"))
    known = {participant.pk: participant for participant in participants}
    shown = [place for place in places if place.participant_id in known and known[place.participant_id].status != Participant.Status.WITHDRAWN]
    names = positions(sum(1 for place in shown if not place.late))
    seats, drawn = [], 0
    for distance, place in enumerate(shown):
        index = None if draw.dealer_seat is None else (draw.dealer_seat + distance) % len(shown)
        position = None
        if not place.late:
            position, drawn = names[drawn], drawn + 1
        seats.append(Seat(known[place.participant_id], distance, index, position, place.late, count=len(shown)))
    for ring, seat in enumerate(sorted(seats, key=lambda seat: seat.participant.join_order)):
        seat.ring = ring
    placed = {place.participant_id for place in places}
    moment = draw.chosen_at or draw.created_at
    return Seating(
        draw, seats,
        unseated=[p for p in participants if p.status == Participant.Status.JOINED and p.pk not in placed],
        fresh=(timezone.now() - moment).total_seconds() < FRESH_SECONDS,
    )
