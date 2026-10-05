"""Each set has its own timer. Server timestamps are the only source of truth.

A set's timer is the sum of its play periods. A player's playing time is the
sum of that player's intervals, which only exist while the set is in play.
Call the writing functions with the session locked.
"""

from django.utils import timezone

from .models import Participant, PlayInterval, PlayPeriod

# Checks that say a player must not get playing time when a set resumes, for
# example because they have already cashed out for good. The app that knows
# registers one.
SKIP_ON_RESUME = []


def open_interval(participant, now) -> None:
    """Start the player's time, unless it is already running."""
    if not PlayInterval.objects.filter(participant=participant, ended_at__isnull=True).exists():
        PlayInterval.objects.create(session_id=participant.session_id, participant=participant, started_at=now)


def close_interval(participant, now) -> None:
    """Stop the player's time. Does nothing if it is not running."""
    PlayInterval.objects.filter(participant=participant, ended_at__isnull=True).update(ended_at=now)


def start(session, now, *, resuming=False) -> None:
    """Start or resume the set's timer and the time of each player at the table."""
    if PlayPeriod.objects.filter(session=session, ended_at__isnull=True).exists():
        return
    PlayPeriod.objects.create(session=session, started_at=now)
    for participant in session.participants.filter(status=Participant.Status.JOINED):
        if resuming and any(skip(participant) for skip in SKIP_ON_RESUME):
            continue
        open_interval(participant, now)


def stop(session, now) -> None:
    """Stop the set's timer and every running player time of this set, all at one timestamp."""
    PlayPeriod.objects.filter(session=session, ended_at__isnull=True).update(ended_at=now)
    PlayInterval.objects.filter(session=session, ended_at__isnull=True).update(ended_at=now)


def _total(rows, now) -> int:
    return sum(int(((ended or now) - started).total_seconds()) for started, ended in rows)


def set_seconds(session, now=None):
    """Seconds on the set's timer, or None if no play was ever timed for it."""
    rows = list(PlayPeriod.objects.filter(session=session).values_list("started_at", "ended_at"))
    return _total(rows, now or timezone.now()) if rows else None


def timers(session_ids, now=None) -> dict:
    """``{session_id: (seconds, running)}`` for the sets that have timed play, in one query."""
    now = now or timezone.now()
    rows = {}
    for session_id, started, ended in PlayPeriod.objects.filter(session_id__in=session_ids).values_list(
        "session_id", "started_at", "ended_at"
    ):
        rows.setdefault(session_id, []).append((started, ended))
    return {
        session_id: (_total(periods, now), any(ended is None for _, ended in periods))
        for session_id, periods in rows.items()
    }


def seconds_by_set(session_ids, now=None) -> dict:
    """``{session_id: seconds}`` for the sets that have timed play, in one query."""
    return {session_id: seconds for session_id, (seconds, _) in timers(session_ids, now).items()}


def is_running(session) -> bool:
    return PlayPeriod.objects.filter(session=session, ended_at__isnull=True).exists()


def player_seconds(session, now=None) -> dict:
    """``{participant_id: seconds}`` for every player who has timed play in this set."""
    now = now or timezone.now()
    totals = {}
    for participant_id, started, ended in PlayInterval.objects.filter(session=session).values_list(
        "participant_id", "started_at", "ended_at"
    ):
        totals[participant_id] = totals.get(participant_id, 0) + int(((ended or now) - started).total_seconds())
    return totals


def running_participant_ids(session) -> set:
    return set(PlayInterval.objects.filter(session=session, ended_at__isnull=True).values_list("participant_id", flat=True))


def player_clocks(session, now=None) -> tuple[dict, set]:
    """``player_seconds`` and ``running_participant_ids`` from one read of the set's intervals."""
    now = now or timezone.now()
    totals, running = {}, set()
    for participant_id, started, ended in PlayInterval.objects.filter(session=session).values_list(
        "participant_id", "started_at", "ended_at"
    ):
        totals[participant_id] = totals.get(participant_id, 0) + int(((ended or now) - started).total_seconds())
        if ended is None:
            running.add(participant_id)
    return totals, running


def format_duration(seconds) -> str:
    """``1 h 05 min``, ``45 min`` or ``under 1 min``."""
    if seconds is None:
        return "not recorded"
    minutes = seconds // 60
    if minutes < 1:
        return "under 1 min"
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes:02d} min" if hours else f"{minutes} min"
