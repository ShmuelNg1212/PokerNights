# Show invite links again: plan

Status: approved 2026-10-16 with the two details as written. Date: 2026-10-16, Asia/Manila. Study: [Show invite links again](../study/1792115569_invite_links_shown_again.md).

## Outcome

A host opens Group settings → Invite players and finds every active invite with its link, ready to copy or share, for as long as the link works. Old links are listed as history. Nothing secret is added to the database.

Mode: Operate. Visual authority: the built Rack in DESIGN.md. Built with the design (impeccable) and motion skills. One migration (a nullable field). No dependency.

## Behaviour

| Where | What the host sees |
|---|---|
| No active invite | "No invite link is active." and the primary **Create invite link**, as today |
| After Create | The page returns to Invite players with the new link as the top row, marked **New**. Copy is ready |
| An active row | "Created by Hana · Oct 16" over "Used 3 of 20 · expires Oct 23, 21:00"; the address in a read-only field with **Copy**; **Share** where the phone has a share sheet; **Revoke** |
| A link made before release, or after `SECRET_KEY` changed | The same line, and "This link was made before links could be shown again." with Revoke. No field |
| With at least one active invite | **Create another link** under the list, a neutral button |
| **Past invites** (collapsed, closed by default) | The 10 most recent dead invites: "Made Oct 2 by Hana · 4 joined · expired Oct 9" (or "revoked Oct 5", or "used up Oct 6"). No address |
| A player | Sees no invite section, as today |
| `INVITE_LINKS_SHOWN=False` | Rows without an address, and the shown-once box after Create, as today. Links made while it was on keep working |

**Share** sends the address with one line, "Join {group} on PokerNights", through the phone's share sheet. Where the phone has none, the button is absent.

## Motion

- **One moment, on Create:** the new row arrives with the `drop` spring from 12px above and 96% size. The New mark draws in under it with the existing `mark-draw` (320ms). It plays once, on the answer to Create.
- **Copy:** the button reads "Copied" for 2 seconds and the field's text flashes Brass for 600ms. No movement.
- **Revoke:** the row leaves with `leave`, and the rows below rise with `shift`. **Past invites** gains the row on the next page.
- **Past invites** opens and closes with the height motion that "More host controls" uses.
- Reduced motion shows every state at once.

## Decisions for the human

The twelve decisions were settled in questions on 2026-10-16 (the study lists them). Approving the plan accepts this list:

1. The New mark stays on the row until the page is left, not for a fixed time.
2. The share text is "Join {group} on PokerNights" plus the address.

## Implementation

Branch `feat/invite-links-shown-again` from `main`. Tests first.

1. **Model.** `Invite.salt`, a nullable `CharField(max_length=32)`. Migration `groups.0006`.
2. **Service (`groups/services.py`).**
   - `invite_token(salt)` = base64url of `salted_hmac("groups.invite", salt).digest()`, without padding.
   - `create_invite` makes a random salt, computes the token, and stores the salt and the token's hash. With the switch off it stores no salt and returns a random token as today.
   - `invite_link_token(invite)` returns the token when the salt is set and its hash matches `token_hash`, and `None` otherwise. Pure; no write; not audited.
3. **View (`web/views.py`, group settings).** Active invites (newest first) with their tokens built into absolute addresses; past invites (revoked, expired or used up), 10 most recent, with how each ended. The new invite's ID comes through the session in place of the address.
4. **Template.** The rows in `_group_settings.html`, reusing `_copy_field.html`, a Share button, and the Past invites disclosure.
5. **Script.** `static/js/invites.js` registered with `page.js`: Share (hidden without `navigator.share`), the arrival on Create, Copy's flash, Revoke's leave.
6. **Switch.** `INVITE_LINKS_SHOWN` in settings and in `doc/wiki/deployment.md`.
7. **Tests.**
   - The token is the same each time and opens the invite. A changed `SECRET_KEY` makes it unshowable while the link still works.
   - A row before the change shows no address.
   - Players never receive an address.
   - Past invites: order, the limit of 10, how each ended, and no address.
   - The switch.
   - Claim and reset links unchanged.
   - Browser check `web/tests/browser/invites.mjs` at 320, 390 and 1280: Copy, Share present or absent, the arrival, Revoke's motion, Past invites, 48px targets, no overflow, reduced motion.
8. **Docs.** The wiki (features and the invite section), DESIGN.md and PRODUCT.md addenda, TODO.md.

## Verification after release

On your phone, in Group settings → Invite players: create a link. It is the top row, marked New. Leave the page and come back; the link is still there, and Copy and Share work. Revoke it; it moves to Past invites.

## Rendezvous (2026-10-16)

Built on `feat/invite-links-shown-again` with the design (impeccable) and motion skills. Released 2026-10-16 as `46557ae`. One migration, `groups.0006_invite_salt` (a nullable field).

- **As planned:** the salt and `salted_hmac` token, rows with Copy and Share, links from before marked, New on the top row after Create, Create another link, Past invites (10, no addresses, how each ended), no audit for viewing, hosts only, the switch.
- **Changed while building:**
  1. **Revoke.** The plan had the row leave with `leave` and the rows below rise with `shift`. That would play before the server answers, which PRODUCT.md rules out. Instead, Past invites' summary takes the accepted-change mark on the next page, as Removed players does.
  2. **Revoke is a quiet action at the left of the row**, apart from Share. The first screenshots had a full red button beside Share in every row.
  3. **"Active" now excludes used-up links.** Before, a link at 20 of 20 uses was still listed with Revoke.
  4. Seven older tests of the shown-once box now run with `INVITE_LINKS_SHOWN=False`, the mode that still has it.
- **Verified:** 1,212 tests on SQLite and on PostgreSQL. `invites.mjs` 17 of 17 at 390, 320 and 1280.
