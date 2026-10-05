# Motion on the live set page: study

Date: 2026-10-05, Asia/Manila. Stage 2 of the [motion overhaul](../plan/1791186717_motion_overhaul.md). The human asked for the Motion AI kit to be applied to this stage.

## The Motion AI kit in this project

- **It is installed.** `.claude/skills/motion/` (ignored by git), `.agents/skills/motion/`, `.codex/config.toml` and `.mcp.json` hold the kit. The last three were committed on 2026-10-04 in `727e2f4` by a commit that added every new file; they contain no secret, only the two public server addresses. The stage 1 notes that say "the AI kit is not installed" are wrong: the agent looked only in the home folder.
- **What is usable now.** The kit's best-practice files work without a server and were read for this study.
- **What is not.** The kit's docs search, spring generator and transition preview run on Motion's server (`https://mcp.motion.dev`), which is not connected in this session; a server listed in `.mcp.json` is picked up when a session starts and is approved. MotionScore audits and the `motion-reviewer` agent need Motion+, which the human declined.

### What the kit's guidance changes

1. **Animate `transform`, not `x`/`y`/`scale`, unless transforms must combine.** A `transform` animation runs in the browser's compositor (off the main thread); the separate properties run in script on every frame. Stage 1 used `y` for sheets and buttons. Sheets move on one axis only and should use `transform`.
2. **`will-change` when the separate properties are used**, set for the animation and removed after it. Applies to toasts (sideways nudge plus vertical stack) and buttons (press plus pulse).
3. **Springs for physical movement, especially if it can be interrupted.**
4. **No overshoot on serious interfaces.** The kit's example is a trading screen. Rows that carry money should move without bounce; bounce stays on small things a finger touches.
5. **No object creation in per-frame callbacks.** Stage 2 uses no per-frame callback.

## What happens on the set page today

The live region is redrawn in two ways:

- **A poll every 4 seconds** (`live.js`): when the set's version changed, `region.innerHTML` is replaced. Every element is new. The redraw waits while the person is typing.
- **The person's own action** (Turbo): the page is morphed, which keeps elements that still match.

After either, `live:updated` fires and `changes.js` compares each `data-watch` element's value with the last one seen. A changed element gets a brass outline for 3 seconds and, on a player row, an "Updated" or "Rebuy added" badge; a new buy-in edge drops onto the stack by a CSS animation. The balanced-books rule reveals once per set.

| Event | Today |
|---|---|
| A player is added | The row is simply there; rows below jump down |
| A buy-in or rebuy | Outline, badge, the edge drops; the outline and badge vanish at 3s without a fade |
| "Still in play" changes | A brass underline appears and vanishes |
| A cash-out, a player leaves | Outline; a "Left" badge is there |
| The set changes state | The whole region is replaced at once |
| A count is confirmed (count-up) | Outline on the row; the progress line changes |
| The books balance | A 600ms reveal of the green rule, once |

## Findings

1. **Rows do not reorder.** Players are listed in the order they joined (`join_order`). The stage table in the programme plan promised "reorder"; nothing on this page reorders. Rows arrive, and rows below them move down. No action removes a row.
2. **Positions can be carried across a redraw by key.** Every row has a stable `data-watch` key. Recording each key's position before the redraw and comparing after it gives the distance to animate (the "FLIP" technique). This works for both the poll and the morph, if both announce the redraw before it happens. Today only the after-event exists.
3. **The browser's View Transition API is the wrong tool here.** Motion's `animateView` wraps it and would do the same job with less code. But while a view transition runs, the page is a picture: taps do not reach the controls. A poll can redraw the page at any moment, so a host's tap would sometimes be lost for a third of a second. This breaks the principle "never in the way". Manual FLIP with `Motion.animate` leaves the page live and can be interrupted.
4. **A state change redraws most of the region** (in play → counting up → finalized). There is no shared element worth carrying. A short cross-fade of the region is enough and is cheap.
5. **Typing.** Redraws already wait while a field has focus, so nothing moves under a count being typed.
6. **Many rows.** A table has at most about ten players. FLIP on ten rows is ten compositor animations.
7. **The first sight of a page must not animate.** `changes.js` already keeps the last seen values per tab, so "new" means new since this person last saw the set, not new since the page loaded.
8. **Money.** Figures appear at their accepted value. A row may slide; an underline may draw; digits do not count (AGENTS.md rule 9).

## Options

1. **Manual FLIP with Motion, keyed by `data-watch`** (recommended). One small module, driven by a new before-event and the existing after-event.
2. **`animateView` for every redraw.** Rejected, finding 3.
3. **Change the poll to morph the region** so elements persist. Larger change to `live.js` with its own risks (typed values, focus, open disclosures are handled by hand today). Not needed for FLIP.

## Verification limit

Browser checks can prove that a row starts displaced and ends in place, that a tap during movement is accepted, and that reduced motion skips it. How it reads at a real table is for the human's phone.
