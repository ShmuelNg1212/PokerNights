# App-like experience on a phone: plan

Status: approved 2026-10-05 with three changes (see the addendum at the end). Date: 2026-10-05, Asia/Manila. Study: [App-like experience on a phone: feasibility](../study/1791172718_app_like_experience.md).

## Outcome

On a phone, PokerNights opens from the home screen like an app, changes screens without a page reload, and updates in place after each action, while staying a server-rendered Django application that works without JavaScript.

This is a staged programme, not one change. **Approving this plan approves the direction and stages 1 and 2 as written here. Stages 3 to 5 each get their own study and plan before any code**, because they depend on a trial whose result I do not have yet.

## Stages

| Stage | What you would notice | Size | Risk |
|---|---|---|---|
| 1. Static caching | Screens appear sooner; nothing looks different | Small | Low, with one deployment unknown |
| 2. Installable app | An icon on the home screen; opens full-screen; an offline notice | Small to medium | Low; needs your iPhone to verify |
| 3. Actions in place | A buy-in, cash-out, count or paid mark updates the screen without a reload and keeps your place | Medium | Medium |
| 4. Screen changes without a reload | Tapping through groups, sessions and sets feels continuous | Medium to large | Medium |
| 5. Feel | Directional transitions, pending states, touch feedback | Small | Low |

### Stage 1: static caching (approved with this plan)

- Fingerprint static file names (Django's manifest storage) in production only; development and tests keep plain names.
- Serve `/static/` with a one-year immutable cache through `vercel.json` headers.
- Prove on a **Vercel preview deployment** that the function can read the manifest, before it goes to `main`. If it cannot, fall back to the cache header with a version query string.
- Measure: requests and time per screen change, before and after, on a throttled connection in the browser check harness.
- No behaviour change. No migration.

### Stage 2: installable app (approved with this plan)

- A web app manifest: name, short name, start address `/`, standalone display, the existing ground colour for theme and background.
- App icons as PNG, generated from the existing chip-and-crescent mark: 180 px for iPhone, 192 and 512 px, and a maskable version. Nothing else raster is added.
- iPhone meta tags for standalone mode and the status bar; safe-area padding checked on every screen.
- **Standalone audit.** Walk every screen with no browser buttons: each must have a way back and no dead end. Add what is missing. Log out and Log in inside the installed app must work.
- **Offline notice.** A small script shows "You're offline. Changes can't be saved until you reconnect." while the browser reports no connection, and removes it on return. A minimal service worker serves a branded "You're offline" page for a failed navigation. It caches no ledger page.
- A short "Add to Home Screen" note for hosts in the wiki; no in-app prompt in this stage.
- No migration.

### Stage 3: actions update in place (own study and plan)

- First, a timeboxed trial on the set page: Turbo against a small module of our own, measured and compared on the points in the study. The study recommends one with the evidence.
- Then: forms submit in the background; the server's fresh HTML is applied without a reload; scroll, typed values, open disclosures and focus are kept; the success toast still appears only after the server accepts; errors appear where they do today.
- Every form keeps working as a native form when JavaScript is off.

### Stage 4: screen changes without a reload (own study and plan)

- Links fetch the next screen and swap the content; history, back and forward, and scroll restoration behave as a browser does; a link is fetched when the finger touches it.
- Every script module gets a start and a stop per visit; the set poll stops when the host leaves the set.
- A shared "visit finished" helper for the browser scripts.

### Stage 5: feel (own study and plan)

- Transitions that show direction (deeper, back), a visible pending state on the control that was tapped, and no layout jump when content arrives. Reduced motion respected.

## Decisions for the human

Approving accepts the recommendations unless you say otherwise.

1. **Direction:** upgrade in place, as you chose. Recommended.
2. **Order:** 1, 2, then 3. Stage 3 addresses your first complaint, but stages 1 and 2 are small, low-risk and make everything after them cheaper to measure. If you would rather feel the action change first, say so and I will start with stage 3's trial.
3. **PNG app icons.** DESIGN.md says the app ships no raster images. I recommend one exception: app icons generated from the existing mark.
4. **A preview deployment for stage 1.** I recommend pushing a branch so Vercel builds a private preview, because the fingerprinting risk can only be seen on Vercel. This does not touch production. You declined a preview once before for a visual check; this one is a technical gate that I can verify myself, without your phone.
5. **A library is allowed if the stage 3 trial favours it.** This records the requirement that AGENTS.md asks for. Recommended, limited to one vendored file with no build step.
6. **Out of scope for the whole programme:** offline recording, push notifications, WebSockets, a native app in the app stores.

## What I cannot verify

- **Anything on a real iPhone:** standalone mode, the home-screen icon, safe areas, and how the screens feel. Stage 2 ends with a checklist for you.
- **Signed-in timings on production:** I have no production account. Timings will be measured locally under throttling and, if you create a test account for me, on production.

## Acceptance criteria

Stage 1:
- AC1. A screen change after the first makes no request for the stylesheet, the font or any script.
- AC2. A changed static file is picked up on the next visit after a release.
- AC3. Development and the test suite run without a collected manifest.

Stage 2:
- AC4. The app can be added to an iPhone and an Android home screen with the PokerNights icon and opens without browser bars.
- AC5. In standalone mode no screen is a dead end, and a signed-out visitor reaches Log in.
- AC6. The offline notice appears and clears, and no ledger page is ever served from a cache.

Every stage:
- AC7. All existing tests pass on SQLite and PostgreSQL, and every flow still works with JavaScript off.
- AC8. Before-and-after measurements are recorded in the stage's plan.

## Out of scope

Listed in decision 6, plus: redesigning any screen, changing any service or money rule, and replacing the 4-second poll.

## Rollback

Each stage is its own release and reverts alone. Stage 1 and 2 have no migration and change no data. An installed home-screen icon keeps working after a rollback; it simply opens the site.

## Addendum, 2026-10-05: the human's approval and three changes

The human approved and said:

1. "i dont need a preview deployment I cant just test the app on the live build on my own phone." Read as: no preview; each stage is released to production and the human tests it on their phone. (My interpretation of "cant" as "can".)
2. "I dont plan on making this a fully functional mobile app yet." Read as: **stage 2 (installable app) is deferred.** No manifest, icons, standalone mode or service worker for now. Decision 3 (PNG icons) is therefore not needed yet. My interpretation; the human can narrow it.
3. "I want an additional last stage to utilize motion.dev and its Motion AI kit from its mcp to kickstart a motion graphics overhaul for the app."

Revised stages:

| Stage | Status |
|---|---|
| 1. Static caching | Approved; built and released in this cycle |
| 2. Installable app | **Deferred** |
| 3. Actions update in place | Own study and plan |
| 4. Screen changes without a reload | Own study and plan |
| 5. Feel | Folded into stage 6 unless its study says otherwise |
| 6. Motion overhaul with Motion (motion.dev) and its AI kit | **New, last.** Own study and plan |

### Stage 1, changed because there is no preview

The planned approach (Django's manifest storage with fingerprinted file names) carried one unknown that only a Vercel build could answer: whether the function can read the manifest at run time. If not, every page would fail in production. Without a preview that risk is not acceptable, so stage 1 uses the fallback the plan named:

- `config.storage.VersionedStaticStorage` appends `?v=<release>` to stylesheet and script addresses. Files keep their names; nothing is read at run time.
- `config.deploy.static_version` derives the tag from Vercel's deployment id, commit or URL. On Vercel with none of them the app refuses to start, so the build fails and production keeps its version, instead of caching unversioned files for a year.
- `vercel.json` headers: `/static/css/` and `/static/js/` are `public, max-age=31536000, immutable`. Fonts, branding and icons are cached for a week with background revalidation and are **not** versioned, because the stylesheet refers to the font by a plain relative address and the preload must match it. To change a font or logo, give the file a new name.
- If Vercel ignores the header rule for static files, the result is today's behaviour, not a failure. This is checked on the live site right after release.

### Stage 6 notes for its study

- This is the recorded requirement AGENTS.md asks for before a front-end library is added. The study must still decide how Motion is loaded without a build step (a vendored file or a pinned CDN module), and its size against the current 21 KB of scripts.
- Rules that bound it: reduced motion disables movement (AGENTS.md rule 9); money figures appear at their accepted value, never counting up (rule 9, PRODUCT.md); the app works without JavaScript.
- Motion's MCP server is not connected in this session. The human needs to add it. Whether its AI kit needs a paid Motion+ plan is unverified. A Motion skill became available in this session and will be used.
- Stage 6 comes after stage 4 on purpose: screen-to-screen transitions cannot be animated across full page reloads in the way an overhaul would want.

## Stage 1 progress, 2026-10-05

Built on `feat/static-caching`, merged into `main` and released as `e229cf6` (previous production commit `77c0fbd`). The release also carried the entry flow fixes that were waiting on local `main`.

Measured on production, signed out, phone-sized headless Chrome on an emulated slow connection (400 ms round trip, 1.6 Mbit down), warm browser cache:

| Screen change | Before | After |
|---|---|---|
| Log in → Sign up | 6 requests (4 re-checks), 927 ms | 1 request, 595 ms |
| Sign up → Log in | 7 requests (5 re-checks), 925 ms | 1 request, 516 ms |
| First visit, cold cache | 8 requests, 2,734 ms | 7 requests, 1,738 ms (one sample each; cold loads vary) |

Checked on the live site: `.css` and `.js` addresses carry `?v=012fdea36b` and answer `public, max-age=31536000, immutable`; the font and logo answer a one-week cache with background revalidation; HTML stays `no-store`.

Verification: 618 tests pass on SQLite (six new in `config/tests.py`). PostgreSQL was not rerun for this stage; it changes no query or write. `collectstatic --dry-run` succeeds with the new storage.

AC1 met for the measured pages (a signed-in set page loads more scripts through the same mechanism; not measured on production, no account). AC2 follows from the per-deployment tag and is confirmed on the next release, when the tag must change. AC3 met.

Not verified: a real phone, and signed-in pages on production.

2026-10-05: the human asked what stage 2 adds, then said “ok i like stage 2. start planning and studying.” Stage 2 is no longer deferred. It has its own study and plan: [installable app](1791176898_installable_app.md).

2026-10-05: stage 3 has its own study and plan, [actions in place](1791178826_actions_in_place.md), with the Turbo-versus-own-module trial. The human chose Turbo. Built and released the same day.

2026-10-05: stage 4 has its own study and plan, [screen changes without a reload](1791181102_screen_changes_without_reload.md), released in two parts (4a script lifetimes, 4b links on).
