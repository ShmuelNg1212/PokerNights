# Session setup menu: study

Date: 2026-10-30. Mode: mixed.

## Request

After a host selects the stakes preset, rake, blinds and buy-in amounts, the app goes to the menu where the host can announce to the group and set the chip values. The New session page can also offer two options: announce automatically, and use a chip preset at creation.

## Current state

- `games.views.session_new` redirects to the set page (`session`). See `games/views.py:76`. The set page shows "Get this set ready".
- The session page (`night`) already is the menu. `templates/web/night.html:45-46` shows the Announce card and the Chip values card. A host reaches it only through the set page's back link.
- `night_announce` takes an optional start time and a seat count. The seat count defaults to the table's seats.
- `services.announce_night` and `services.set_chip_values` each lock the session, write the audit record and increment the version. Both can run in the transaction of `create_session`, so a refusal rolls back the new session as well.
- Push notices go out after commit (`notify.tell_night`, `push.after_commit`). A rollback sends nothing.

## Findings

1. **The redirect is one line, but tests and one browser script depend on it.** `games/tests/test_sessions.py:178` and `games/tests/test_form_layout.py:94` assert the set page. `web/tests/browser/session_setup.mjs:56` and `rake_controls.mjs` continue from the page after creation.
2. **ADR 0005 conflicts with the request.** It says: "A new session still starts without chip values. No preset applies automatically." An explicit choice on New session is not automatic, but the first sentence must change. This needs a new ADR and a spec edit after approval.
3. **Creating a session has no `request_id`.** The form also has no `data-once`. Today a double tap makes two drafts that only hosts see. With automatic announce, a double tap makes two announced sessions and tells every player twice. Design rule 3 requires a `request_id` here. This change must add it. `GameNight` needs a nullable field and a conditional unique constraint.
4. **Units must match.** Nothing converts pesos and chips (ADR 0001, ADR 0005). The Unit field and the stakes preset can change the unit after the page loads. The chip preset list must follow the unit in the browser, and the server must refuse a mismatch.
5. **A chip preset and a stakes preset stay separate.** ADR 0005 says they are not linked. Choosing a stakes preset must not choose a chip preset.
6. **Two primary buttons.** A host on a draft session sees "Open set 1" and "Announce to the group", both primary. This page now is the first screen after creation, so its hierarchy needs a design pass.
7. **One more tap to play now.** A host who plays at once must select "Open set 1" after creation. This follows from the request.
8. **The home and group cards still go to the set page** for a draft ("Open set N"). The request does not cover them.

## Options for the two settings

| Option | For | Against |
|---|---|---|
| A. Choice per session on New session, off by default | Matches the request. Nothing tells players by surprise. No group setting. | The host selects again for each session. |
| B. Group default in Group settings, plus the choice per session | Fewer taps for a regular game. | More to build. A saved default can tell the whole group by accident. |

Recommendation: A. Option B can follow later without rework.
