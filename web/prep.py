"""Preparing a set: which steps are done and which is next (DESIGN.md, "Set page").

Read from what the set page already loads; no query is made here.
"""

def states(session, summary, me):
    """Each step's state for the host of a draft or open set, else None. Stakes are chosen when the session is made."""
    if not me.is_host or session.state not in ("setup", "open"):
        return None
    seated = summary.player_count > 0
    return {"players": "done" if seated else "next", "next": "start" if seated else "players"}
