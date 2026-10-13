# A picture for the link: plan

Status: approved 2026-10-13 ("approved, i want the same card for invite links as well"). Built, not released. Date: 2026-10-13, Asia/Manila. Study: [A picture for the link](../study/1791861227_link_preview.md).

## Outcome

A PokerNights link pasted into Messenger, WhatsApp, iMessage, Telegram or Slack shows a card:

- **Picture:** 1200 × 630, the showcase design laid out again: logo, "Who pays whom, worked out." and the phone with the live set screen.
- **Title:** PokerNights
- **Line:** Records buy-ins and cash-outs for a home poker game and works out who pays whom. It does not move money. (The same sentence as the install manifest.)

Every page carries the same card. It names no group and no person. No migration, and no screen changes.

## Decisions for the human

1. **The card's words** above. Say if the title or the line should read differently.
2. **Invite links.** They get the same card (study, option A). Say if the invite page should instead be titled "You're invited to a game on PokerNights" (option B).

## Implementation

Branch `feat/link-preview` from `main`.

1. **The picture.** `doc/showcase/link-preview.html` next to the thumbnail's source, rendered with headless Chrome to `static/branding/link-preview.png`. The logo and headline sit inside the middle square so a square cut keeps the name. Kept under 300 KB; a JPEG instead if the PNG cannot get there.
2. **`config/pwa.py`** (the context processor that already feeds `base.html`): one more value, the picture's full address, built from the request and the static path.
3. **`templates/base.html`:** `<meta name="description">`, the `og:` tags (`title`, `description`, `type`, `site_name`, `image`, `image:width`, `image:height`, `image:alt`) and `twitter:card`. No `og:url`, because invite, reset and claim addresses contain a token.
4. **Tests** in `web/tests/test_branding.py`:
   - the log-in page, fetched logged out, carries each tag, and the picture's address starts with `http` and the host;
   - the invite page carries the same card and no `og:url`;
   - the file exists, is 1200 × 630 and is under 300 KB.
5. **Suites.** Django on SQLite; PostgreSQL before release.
6. **Documents.** Wiki features and deployment (a changed picture needs a new file name), the DESIGN.md sentence about raster imagery, TODO.md.

## Acceptance

1. After release, a PokerNights link pasted into a chat shows the picture, the title and the line.
2. An invite link shows the same card and still works once opened.
3. Nothing on any screen of the app looks different.

## Fail-safe

The change adds tags and one file. If the picture's address were wrong, a chat app would show the card without a picture, as it shows no card now. The way back is a revert of the commit.

## Not covered

- A chat app that already fetched a link keeps its old, empty preview for a while. A new invite link is a new address and is not affected.
- Checking the card needs the live site: a chat app cannot reach a local server. After release, one fetch of the log-in page and one of the picture, about four minutes after the push, then the human pastes a link into a chat.

## Release

Kept local until you say to push.

## Progress

2026-10-13: Decisions: the card's words stand as written; invite links get the same card (option A). Built on `feat/link-preview`.

- `static/branding/link-preview.png`: 1200 × 630, 254 KB, rendered from `doc/showcase/link-preview.html` with headless Chrome. The logo and headline are inside the middle square. One addition to the described design: a faint oversized mark at the left edge, because keeping the words inside the middle square left that side empty.
- `config/pwa.py`: `link_preview_image`, the picture's full address from the request.
- `templates/base.html`: the description, the `og:` tags and `twitter:card`. No `og:url`.
- **Found while testing:** a signed-out fetch of an invite link is redirected to sign-up. That page carries the card, so an invite link shows it. The study's item 3 is corrected in an addendum.

Verification:

- Three new tests in `web/tests/test_branding.py`: the home address and an invite link, both fetched logged out and followed, carry the card with a full picture address and no `og:url`; the invite page's head names no group and holds no token; the file is a 1200 × 630 PNG under 300 KB.
- 1,098 tests pass on SQLite (15 skipped) and on PostgreSQL 17 (1,095 before).
- The picture was looked at as rendered.

Not verified: any chat app. That needs the live site.

Documentation synced: wiki (features, deployment, journal), DESIGN.md, PRODUCT.md, TODO.
