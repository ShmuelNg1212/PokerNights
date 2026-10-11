# Suggest adding the app to the home screen: study

Date: 2026-10-11, Asia/Manila.

## Request

The human said: "after a user signs up or logs in the browser, can we add a popup to recommend the user to save the webapp to home screen so it feels close to a real native application."

## What happens today

- The site is installable since 2026-10-05: a manifest, icons, a service worker with an offline page, iPhone meta tags. Added to a home screen it opens full-screen.
- Nothing tells a person this. The installable-app plan left "an install prompt" out on purpose; the steps are written only in the wiki.
- After a login or a sign-up the next page plays the arrival once (`config/door.py`: the `arrived` cookie makes `door.welcome` true on the first page shown, and `base.html` writes `data-welcome` on `<main>`). That is an existing, server-decided "this person just came in" signal, which a prefetch does not consume.

## How a phone lets a site be added

| Where the person is | What the page can do |
|---|---|
| Chrome, Edge or Samsung Internet on Android | The browser raises `beforeinstallprompt` when the site qualifies. The page can keep that event and, on a tap, open the browser's own Install dialog. One tap installs |
| Safari on iPhone | No way to start it from the page. The person taps Share, then Add to Home Screen. The page can only show those steps |
| Chrome or Firefox on iPhone | Since iOS 16.4 their Share menu has Add to Home Screen too. Same steps |
| A browser inside a chat app (Messenger, Viber, Instagram) | Cannot add to the home screen. The person must open the page in Safari or Chrome first. Invite links arrive this way |
| Already opened from the home screen | `display-mode: standalone` (or `navigator.standalone` on iPhone) is true. Nothing to suggest |
| A desktop browser | Chrome can install it as a window. "Home screen" does not apply |

## Findings

1. **The page cannot know that the app is installed** when it is opened in the browser. It only knows when it is running as the installed app. So a person who installed it and later logs in from Safari again would be asked again, unless the browser remembers the answer.
2. **Where to remember "not now".** A browser-side note (`localStorage`) fits: the suggestion is about this browser on this phone, not about the account. It needs no migration and no write on the server. A second phone asks once more, which is correct.
3. **On iPhone the installed app has its own login.** It does not share Safari's cookies (wiki, "Put PokerNights on your phone"). A person who follows the steps meets the login screen again. The popup must say so, or the first run of the "app" looks broken.
4. **Timing.** The arrival after login runs for under a second and ends on the first tap. A popup over it would hide it and could take that tap. It should come after the arrival, and not on a page where the person has a job waiting: the join and claim confirmation pages, or a session's closing recap, which opens by itself.
5. **Android's event may not come.** It is raised only when Chrome judges the site installable and not installed, sometimes a few seconds after load, and not at all in some browsers. Without it the Android card can only show the menu steps.
6. **The in-chat browsers are where most invites open.** Suggesting "Add to Home Screen" there fails. The honest message is "open this in Safari (or Chrome) first", with a button that copies the address.
7. **Design.** DESIGN.md: a bottom sheet is the pattern for one focused task, with the `sheet` spring. The existing sheet script serves only the set and session pages (`#table-sheets`); this popup appears on any page, so it needs its own small dialog that reuses the sheet's look. The craft rule "no modal for a task that needs neither interruption nor protected focus" applies: this is a suggestion, so it must be dismissible at once, appear once, and never return on its own after "No thanks".
8. **No dependency, no server write.** One template partial, one script, CSS, and a context flag. The step pictures are drawn as inline SVG in the app's own stroke; iPhone's Share glyph is redrawn, not copied from Apple's artwork.
9. **The user tests on the live build.** A failure must leave the page as it is today: the script does nothing unless every check passes.

## Options

| Option | For | Against |
|---|---|---|
| A. A bottom sheet once after coming in, then a permanent quiet entry to find it again | Seen by everyone once; never nags; findable later | A modal moment right after login |
| B. A card on Your groups until dismissed | No interruption | Easy to ignore; only on one page; not "a popup" as asked |
| C. A sheet on every login until installed | Most installs | Nags; cannot tell that it is installed when opened in the browser |

Recommend A: the sheet once, plus "Add to home screen" under the account controls for later.

## Risks

| Risk | Effect | Answer |
|---|---|---|
| The steps are wrong for the person's browser | They cannot find the button | Three variants chosen from what the browser reports; the generic one names both menus |
| The popup covers something the person came to do | Annoyance at the first use | Shown only on ordinary pages, after the arrival, closed by one tap, Escape or a tap outside |
| Asked again after installing | Looks careless | Never shown inside the installed app; "Done, it's on my home screen" and "No thanks" are both remembered |
| iPhone asks to log in again | Looks broken | The sheet says it in one line |
