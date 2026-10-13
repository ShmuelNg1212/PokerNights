# A picture for the link: study

Date: 2026-10-13, Asia/Manila.

## Request

The human said: "I wanna add a thumbnail for the link itself as well." This follows the showcase thumbnail made the same day (`doc/showcase/thumbnail.png`, 1600 × 900, not part of the app).

## What happens now

Read from the code; not yet checked with a chat app.

1. `templates/base.html` has no `og:` or `twitter:` tags and no `<meta name="description">`. No template adds any.
2. A chat app that fetches a PokerNights link therefore shows the page title at most, with no picture and no description.
3. A person who is not logged in only reaches the public pages: log in, sign up, the invite page (`/join/<token>/`), the password reset page and the claim page. The home address answers with a redirect to log in, which a chat app's fetcher follows. All of these extend `base.html`.
4. Most links people send each other are invite links: PRODUCT.md says "An invite link is the way in."

## What a preview needs

- `og:title`, `og:description`, `og:image` with its width, height and alt text, `og:type`, `og:site_name`, and `twitter:card` set to `summary_large_image`.
- The picture's address must be a full address with `https://` and the host. `{% static %}` gives only a path, so the host has to come from the request. Nothing in the app does this for a static file yet; `groups/views.py` does it for invite links with `request.build_absolute_uri`.
- 1200 × 630 is the size the large card uses in Messenger, WhatsApp, iMessage, Telegram and Slack. Some of them show a small square cut from the middle instead, so the name has to survive that cut.
- WhatsApp has dropped pictures above about 300 KB in the past. Staying under it costs nothing.

## Constraints found

- **Fonts and pictures keep one address** (`config/storage.py`): only CSS and JS get `?v=`. `vercel.json` caches `/static/branding/` for seven days, and chat apps keep their own copy longer. A later change to the picture needs a new file name to be seen.
- **Tokens.** An invite, reset or claim address contains its token. `og:url` would repeat that address in the page, so it is left out.
- **A fetcher opens the link.** Checked: the invite, reset and claim pages change nothing on a plain fetch; each needs a submitted form. A preview does not use up a link.
- **DESIGN.md says the build ships no raster imagery.** The app icons in `static/icons/` are already PNG files; this adds one more file that no screen shows.
- **`test_branding.py`** checks the four SVG logos by name. A PNG beside them does not disturb it.

## Options

| Option | For | Against |
| --- | --- | --- |
| A. One card for every page: the name, one line, one picture | Smallest change; nothing about a group or a person leaves the app | An invite link reads the same as any other link |
| B. As A, and the invite page has its own title, "You're invited to a game on PokerNights" | The link people send most says what it is | One more string; still names no group |
| C. The invite card names the group | Most personal | The group name becomes readable by anyone holding the link, and by the chat app's servers, before login |

Recommended: A now. B is a one-line follow-up if the human wants it. C is not recommended.

## The picture

The showcase thumbnail does not fit as it is: it is 16:9, and its description line would be too small in a chat bubble. The link picture is the same design laid out again at 1200 × 630: logo, the headline "Who pays whom, worked out." and the phone with the live set screen. The description line moves into the preview's own text.

## 2026-10-13 addendum

Item 3 of "What happens now" was imprecise. A signed-out fetch of an invite link does not show the invite page: it is redirected to sign-up (`groups/views.py`, `accept_invite`). Sign-up extends `base.html`, so the conclusion holds. The human chose option A.
