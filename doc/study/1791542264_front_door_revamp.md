# Front door revamp: study

Date: 2026-10-09, Asia/Manila. Request: "I want the initial user experience (log in and sign up) to feel more premium … cool animations and a revolutionary UI. Use motion and UI design skills."

Skills used for this study: the design skill (impeccable, `shape`) and the motion skill (best practices for vanilla JavaScript). The Motion+ audit server is not signed in, so no MotionScore audit was run; the plan measures in the browser instead.

## What the human chose (2026-10-09)

Asked three questions before this study was written:

1. **Direction:** "The chip comes alive". The chip-and-crescent mark is the hero and the one actor on the page. No new colour or imagery.
2. **Scope:** the whole front door. Log in and Sign up get the full treatment; the pages that share their frame get the new frame and a quieter arrival.
3. **Arrival:** about one second, never blocking. Full once per browser session, a short version after. This is an exception to DESIGN.md's 900ms limit for a signature moment.

## What is there today

Seven screens share one frame (`.entry-page`, `partials/entry_head.html`, `partials/entry_field.html`):

| Screen | Template | Seen |
|---|---|---|
| Log in | `registration/login.html` | signed out |
| Sign up (plain and invited) | `accounts/signup.html` | signed out |
| Sign-up needs an invite | `accounts/signup_closed.html` | signed out |
| Set a new password, and its dead link | `accounts/reset.html` | signed out |
| Join group, and a broken invite | `groups/invite_accept.html` | either |
| Claim a player, refused and dead links | `groups/claim.html` | either |

The frame is one centred 440px column on the ground colour: the mark at 72px as an `<img>`, "PokerNights" at 2rem, a three-line description, a centred heading, the form, one alternate line. Nothing separates the brand from the task; the page is flat text on near-black.

**Movement today.** The primary button sinks and springs back. A refused field is nudged. The claim page's player token springs in (`[data-pop]`). Between Log in and Sign up there is the plain 180ms cross-fade, because entry pages state no depth. That is all. The rest of the app has a full motion system that these pages do not use.

**How the forms travel.** Log in, Sign up and the others post natively (Turbo forms are opt-in), so an accepted login is a full page load. The stylesheet already says `@view-transition { navigation: auto; }`, so a browser that supports it animates between the two documents. Links between entry pages go through Turbo and use the same-document view transition.

**Known limits recorded earlier.**

- An invited Sign up is 848px tall at 390px wide, four pixels over an 844px phone. A refused Sign up needs a scroll.
- The repeat critique (25 of 40) said the hierarchy "still serves the brand" and asked to make the invitation the subject: group name as the heading, compact mark, shorter password help. This is an open item in TODO.md.

## What "premium" has to mean here

PRODUCT.md and DESIGN.md set the edges. Dark, warm, tactile; plain exact words; no casino imagery; no raster decoration; reduced motion respected; 48px targets; 4.5:1 text. So premium cannot come from a picture, a glow or a new palette. It comes from three things the pages lack:

1. **A subject.** One thing the eye lands on, drawn with care: the chip.
2. **Depth.** Two surfaces instead of one: the night above, a raised sheet below that holds the task. The app's own sheets and buttons already have this vocabulary (rail surface, 26px corners, a solid underside).
3. **An answer to every touch.** Arriving, typing, sending, being refused, getting in: each has a movement that says what happened.

## Findings that shape the plan

1. **The mark must become inline SVG.** An `<img>` cannot have its ring and crescent moved separately. The mark is four shapes; a partial can carry it. The file in `static/branding/` stays for the icon and the header.

2. **The arrival must be CSS, not Motion.** Scripts are deferred. A script-driven arrival paints the finished page for a frame and then jumps back to the start; this is the recorded footgun `motion_starts_a_frame_late.md`. CSS keyframes that run *from* a start state *to* the element's ordinary state begin on the first paint, need no script, and leave a complete page if they never run. The motion skill's spring generator gives the app's `sheet`, `arrive` and `shift` springs as CSS `linear()` curves, so the arrival matches the rest of the app. Safari before 17.2 ignores `linear()` and gets the app's ease-out.

3. **Motion (the library) is for what a finger causes.** The chip turning as keys are typed, spinning while a form is sent, shaking on a refusal. These are interruptible springs on `transform`, through the existing `pokerMotion.run`.

4. **The server chooses which arrival plays.** "Full once per browser session" must be known before the first paint, so a script reading storage is too late. A session-lifetime cookie set by the entry views (no database write, no Django session) lets the template write `data-arrival="full"`, `"short"` or nothing. A page that comes back refused (a POST) gets nothing: the chip shakes instead.

5. **Getting in can be one continuous movement.** If the hero chip and the top bar's mark share one `view-transition-name`, the browser carries the chip from the middle of the entry page into the top bar of Your groups as the login lands, and back out on Log out. It needs Chrome 126 or Safari 18.2. Anywhere else the screens change as they do today. It must be proven in a probe before it is relied on: a native POST followed by a redirect is the case to check, on iPhone Safari and in the installed app.

6. **Log in and Sign up can be one place.** With names on the chip, the wordmark and the sheet, the same-document view transition resizes the sheet and moves the chip between the two screens while the fields fade. Today the whole screen cross-fades.

7. **Only `transform` and `opacity` move, with one candidate exception.** Archivo's width axis is the system's signature (compressed figures). The wordmark widening from 62% to 88% as it arrives would be a movement only this brand has. It is a layout property, so it runs on the main thread: one short centred line, once. It is kept only if the browser check shows no late frame at 4× CPU slowdown; otherwise the wordmark fades and rises like everything else.

8. **Height is the tight constraint.** A sheet adds padding. The hero must shrink where the form is long: a 96px chip over the wordmark on Log in; a compact row (56px chip beside the wordmark) on Sign up and Set a new password. The description moves to the foot of the sheet on the long forms. Target: the empty Sign up, invited or not, shows its button without a scroll at 390 × 844.

9. **Password managers must not notice.** Field names, `autocomplete` values, the native POST and the two-field layout stay exactly as they are. This rules out the one-step-at-a-time idea, which the human also declined.

10. **Nothing perpetual.** No idle loop, no ambient drift. A phone at a poker table is on battery, and DESIGN.md's first motion principle is that motion explains. The chip is still unless something happened.

## Risks

| Risk | Answer |
|---|---|
| The entry pages are the only way in; a fault locks everyone out | Every movement runs from a complete, visible page. No element is hidden until a script shows it. One switch, `DOOR_MOTION=False`, removes all new movement without a release |
| The human tests on the live site, not a preview | Same as above; plus a browser check with Motion blocked, JavaScript off, and reduced motion |
| The hand-over into the top bar misbehaves on iPhone | Probe first. It is a progressive extra; the switch turns it off |
| The arrival annoys on the tenth visit | Full version once per browser session; any key or tap ends it; the username field has focus from the first frame |
| A taller frame pushes the button off a small phone | Measured at 320 × 568, 390 × 844 and 1280 × 800 for every screen, empty and refused |
| The autofocused field and the iPhone keyboard | The sheet is in the page's flow, not fixed to the bottom edge, so the recorded keyboard footgun does not apply |

## Not studied

A password-strength meter, email or social login, a marketing page, and sound or haptics. None was asked for.
