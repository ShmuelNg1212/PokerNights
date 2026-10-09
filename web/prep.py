"""Preparing a set: which steps are done and which is next (DESIGN.md, "Set page").

Read from what the set page already loads; no query is made here.
"""

STEPS = ("players", "stakes", "open", "start")


def states(session, summary, me):
    """Each step's state for the host of a draft or open set, else None. Stakes are chosen when the session is made."""
    if not me.is_host or session.state not in ("setup", "open"):
        return None
    done = {"players": summary.player_count > 0, "stakes": True, "open": session.state == "open", "start": False}
    upcoming = next(key for key in STEPS if not done[key])
    result = {key: "done" if done[key] else ("next" if key == upcoming else "later") for key in STEPS}
    result["next"] = upcoming
    return result
