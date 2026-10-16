# Show invite links again: study

Date: 2026-10-16, Asia/Manila.

## Request

The human said: "I want the option to see previously created invite links. grill me while planning and studying." The decisions below were settled in three rounds of questions on 2026-10-16.

## What happens today

- **Create invite link** (Group settings → Invite players, hosts only) makes a link that lasts 7 days and 20 uses (`groups/services.py`, `INVITE_DAYS`, `INVITE_MAX_USES`).
- The token is `secrets.token_urlsafe(32)`. Only its SHA-256 is stored (`Invite.token_hash`). The link is put in the session and shown once, in a green box with Copy, on the next page ("It is shown only once.").
- Under the button, each active invite is a row: "Expires Oct 23, 21:00 · used 3 of 20" and Revoke. There is no address, because the server does not have it.
- Expired, revoked and used-up invites are not shown anywhere.
- So a host who lost the link has to create a second one. Two live links for one group are two things to track and revoke.

## Findings

1. **Links made before this change cannot be shown.** Their tokens were never kept. They keep working until they expire, within 7 days.
2. **The token can be made reproducible without storing it.** A random `salt` stored on the row, and the token computed as an HMAC of that salt under the server's `SECRET_KEY` (Django's `salted_hmac`, which the session and password-reset machinery already rely on). The row keeps only the salt and the hash. The salt alone, from a database copy, opens nothing. 32 bytes of HMAC, base64url, give a 43-character token, the same shape as today's.
3. **Changing `SECRET_KEY`** leaves every existing link working, because the hash was stored when it was made. The server can no longer produce those links, and it can tell: the recomputed token's hash no longer matches. Such a row reads as a link that cannot be shown.
4. **Only hosts see the section** (`{% if me.is_host %}` in `templates/web/_group_settings.html`). Players never see these links.
5. **Claim and reset links work the same way and stay shown once.** Each hands over one player or one account; a reset link is a way to log in as that person.
6. **What exists to reuse:** `web/_copy_field.html` with `copy.js` (the read-only field and Copy), `navigator.share` handling in `share.js`, the `*-arrived` marks for something just added, and the `shift` and `drop` presets in `motion.js`.

## Decisions (settled 2026-10-16)

| # | Question | Answer |
|---|---|---|
| 1 | The job | Copy an active link again. Dead links are history, without their address |
| 2 | How the link is shown again | Computed from a stored salt and `SECRET_KEY`; no token stored |
| 3 | Who sees links | Any host of the group |
| 4 | Claim and reset links | Unchanged, shown once |
| 5 | Links made before release | Keep working; the row says it cannot be shown |
| 6 | An active row | The address in a read-only field, Copy link, Share where the phone has it, Revoke, and "Created by Hana · Oct 16 · used 3 of 20 · expires Oct 23, 21:00" |
| 7 | After Create | No separate box. The new link is the top row, marked New, with the app's arrival mark |
| 8 | Past invites | A collapsed section, the 10 most recent, no address: made when and by whom, how many used it, how it ended |
| 9 | Audit | Create and revoke as today. Viewing and copying are not recorded |
| 10 | Switch | `INVITE_LINKS_SHOWN`, on by default. Off returns rows without an address and the shown-once box |
| 11 | The create button | With an active link: a quieter **Create another link** under the list. With none: **Create invite link** at the top, as today |
| 12 | Extending a link | Out of scope. A possible follow-up |

## Risks

| Risk | Effect | Answer |
|---|---|---|
| Someone with a host's unlocked phone opens Group settings | They can copy a live invite | The same person could create one today. An invite only lets someone join as a new player; it moves no money and grants no host role. Revoke stays one tap |
| The database leaks | No live link can be rebuilt from it without `SECRET_KEY` | The design choice in finding 2 |
| `SECRET_KEY` is rotated | Live links stop being showable but still work | The row says so; Create another link |
| The address sits in the page's HTML | A cached or prefetched copy holds it | The page is host-only, signed-in and already `no-cache` for Turbo; today's once-shown box was in the HTML too |
