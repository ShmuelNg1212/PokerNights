# Features

What the app does today (Stage 1). Items that are planned but not built are listed at the end.

## Accounts and groups

- Sign up, log in, log out.
- Create a group. The creator is a host.
- A host creates an invite link (valid 7 days, 20 uses, revocable). A signed-in person who opens it becomes a player.
- A host adds a player to the roster by name, without a login. The host acts for that player.
- A host renames or removes a member, and makes a member with a login a host. A group always keeps one host.
- A person outside the group gets "not found" for everything in it.

## Tables and presets

- A table has a name and 2 to 12 seats.
- A preset saves stakes: blinds, game type, minimum and maximum buy-in, the usual buy-in, and the unit.
- Editing a preset changes no existing game.

## Units

- Each game counts in **pesos** (the default) or in **chips**. The host selects the unit on the preset or when creating the game.
- In a pesos game, each figure is a peso amount: buy-ins, cash-outs, results and transfers.
- In a chips game, each figure is a chip count, shown as "1,600 chips". A chips game has no peso value. No ₱ appears on its screens, and its transfers are in chips.
- The app does not convert between chips and pesos.
- The unit of a game cannot change after the first accepted buy-in.

## Sessions and sets

- A **session** is one gathering at one table on one date. It holds one or more **sets**, played one after another.
- Each set has its own buy-ins, cash-outs, balance check, results and timer. A new set starts money-free. Before play starts, the host can record fresh opening buy-ins with the default start option.
- After play of a set has ended, the host taps **Start next set**. The new set has the same table and settings and the players who were still at the table. The host can add or remove players before starting it.
- Who pays whom is worked out **once per session**: the host taps **Close session and settle up** when every set is finalized or canceled. The list nets each player's results over all sets.
- A closed session cannot get another set.

## Timers

- Each set has its own timer. It starts when the host starts the set and stops when the host ends play. If the set is resumed, the timer continues; the time spent counting is not added.
- Each player's playing time in a set is the part of that timer during which they were at the table. A late joiner starts later; a player who leaves stops earlier.
- All times come from the server. A reload or another tab shows the same figure.
- Playing time is stored with each frozen result. Sets played before this feature show "not recorded".

## End of a set

1. **End play.** The set's timer and every player's time stop at one moment.
2. **Confirm final counts.** The host types what each player has left, for as many players as are counted, then confirms. Each "Confirm count" button and "Confirm all counts" confirm every typed count at once. 0 is a valid count. An empty field is skipped and stays "Awaiting count"; it is never treated as zero. If one value is refused, nothing is saved and the typed values stay in their fields.
The live stack counter adds remaining counts, accepted cash-outs and collected rake, then compares the sum with gross buy-ins. The host preview updates while typing; a valid draft replaces a saved count. A blank field uses its saved count, or stays uncounted if none exists. Zero is valid. Missing players and invalid entries prevent a complete match. Final-cashed-out players contribute only through cash-outs, so their saved counts are not added twice. Overrides stay outside this raw stack check. Unsaved totals are labelled Preview; confirmation and cash-out remain separate. Players and JavaScript-free views see confirmed totals only.

3. **Statuses.** Each player is "Awaiting count", "Ready to cash out" or "Cashed out".
4. **Cash out counted players (N).** The host reviews the counted players, each amount and the total, then confirms once. All of them are cashed out, or none. Players still to count stay pending; the host runs the action again later.
5. **Stale review.** If a count changed or a player was cashed out elsewhere after the review opened, nothing is recorded and a fresh review is shown.
6. **Finalize the set.** Needs a final cash-out for every player and balanced books (or an override). This freezes the set's results. It lists no transfers.

The individual cash-out still exists: tap the row's Cash out button during play (for early departures), or expand "Details" while counting. Without JavaScript, expand the player row’s Cash out form.

## A game night (one set)

1. **Create.** The host picks a table, date, location, game type, unit and stakes. The game starts as a draft that only hosts see.
2. **Open.** Players join from their phones. The host adds roster players. A full table refuses the next join. A second tap on "Join" adds nothing.
   - **Add players.** A host can add several players in one action: tick them in a searchable list, check the count against the free seats, and confirm once ("Add 4 players"). Everyone selected is added, or nobody is. Players at the table cannot be ticked. If someone else changed the roster first, nothing is added and the selection is kept for review. Adding players records no buy-in and no payment. Add players stays available during play even when every roster member is seated. The same page offers Add new player: enter a name to save a no-login roster identity and join them to the current set in one action. The new player’s timer starts when they join; record their buy-in separately. Duplicate names direct the host to roster selection, or back to the set if that player is already seated, and a full or ended set adds nobody.
3. **Start play and opening buy-ins.** Start the set includes a checked option to add the set’s usual buy-in for each player at the table without an accepted buy-in. Existing buy-ins are kept, even at a different amount. Uncheck the option to start without automatic entries. Records and timers commit together; repeated confirmation creates nothing twice. Each new set uses its own current settings. Resume and late joining add no automatic buy-in. A reversed-only player qualifies again before first start; uncheck when that is intentional.
4. **Buy-ins and rebuys.** The host records each one (a player with a login can record their own rebuy; see “Player rebuys and player-entered counts”) with an amount between the minimum and the maximum. Each record keeps its amount and time. Each player has a running total. On the active set, tap the row’s Buy-in or Rebuy button and confirm to record the default amount. The sheet also offers minimum, default, twice default (capped at maximum), and maximum amounts.
5. **Live view.** Each member sees the player count, buy-in count, the total bought in and the amount still in play. A change by someone else appears within about 5 seconds.
6. **Cash-outs.** The host types the amount a player leaves with, in the game's unit. A player can cash out in several steps and can leave early.
7. **Balance check.** After play ends, the screen compares cash-outs plus collected rake with gross buy-ins. A difference is shown as an amount, with its direction and likely causes.
8. **Corrections.** A wrong buy-in or cash-out is reversed with a reason. The reversed row stays in the log.
9. **Override.** If the error cannot be found, the host records a note and who absorbs the difference: one named player or all players equally.
10. **Finalize the set.** Its results are frozen. Each player sees profit or loss for the set.
11. **Close the session.** The app lists who pays whom with the minimum number of transfers. The host marks each transfer paid, and can undo it. The session shows unsettled, partly settled or settled.
12. **Set log.** Each member can read the players, settings, each buy-in, reversal and cash-out, overrides, results, and who did what and when. Transfers and payment records are on the linked session page.

A game without accepted buy-ins can be canceled with a reason. A canceled game does not count.

## Rake

New session offers Off (default), Flat amount, and Percentage of buy-in before the first buy-ins. On an empty draft or open set, Choose rake before buy-ins opens the same settings. Only the chosen value applies; unused value fields do not block a save. Percentage accepts 0.01%–99.99%, with at most two decimals. It rounds down separately per buy-in to a centavo or whole chip. Flat rake uses the set's unit. The amount entered for a buy-in is gross: ₱1,000 at 5% gives ₱950 in play and ₱50 collected rake. The fee must leave a positive playable amount.

Every buy-in and rebuy uses the rule, including default opening buy-ins and manually recorded late-player buy-ins. Rake stays locked while accepted buy-ins or cash-outs exist. Reversing all accepted money allows reconfiguration. Ordinary stakes edits keep the rule; next sets inherit it. A permitted unit change resets it to Off. Presets do not configure rake.

The set shows gross bought in, collected rake and available to play. Counts/cash-outs plus rake must match gross buy-ins; rake does not replace a missing player's cash-out. Final results include the fee as a loss. Settle-up excludes this already-collected fee, so it is never charged twice and the rake account receives no transfer.

Group settings shows the group's lifetime collected rake across all sessions and sets, including games in progress. Peso and chip totals stay separate. Expand the session/set breakdown to see where each total came from. Reversing a buy-in excludes its fee; payment marks and Undo do not change rake totals. Historical records start at zero rake.

## Collapsible host dock

- On a phone, the host dock on the set page starts with a “Host controls” row. Tapping it folds the dock to one bar; tapping again opens it. It exists in draft, open, in play and counting up.
- The collapsed bar names the next step. In count-up it shows the live count verdict, which follows typed counts.
- No action can be taken from the collapsed bar. Expanding shows every control, option and line of guidance.
- The choice is kept per browser (`localStorage` key `rack-dock`) for all sets, and holds through live updates and state changes. It starts expanded.
- The dock slides open and closed (320 ms and 200 ms); reduced motion switches at once. It moves by transform, so the page is laid out once per slide; a page scrolled to its end glides down with a folding dock.
- In count-up the bar shows the running total (“₱1,900 of ₱2,000 bought in”) and the verdict, both updated as counts are typed. Since 2026-10-05 it does so open as well as folded, and it is the host's one total on a phone (see “Count-up, review and finalize”).
- Since 2026-10-05 count fields use the in-app numpad on a phone, so the next point applies only to text fields on the set page (a cancel reason, an override note, a reversal reason).
- On an iPhone, while the keyboard is up, the dock sits on top of the keyboard as the bar and returns to its saved state when the keyboard closes. Typing in a field inside the dock keeps it expanded. The bar stays the bar and stays on the keyboard while the page is scrolled with the keyboard open, and only a new focus moves the page. `dock.js` reads `window.visualViewport` and sets `--kb` (the dock's offset), `--kb-h` (the keyboard's height) and the classes `kb-open` and `kb-bar` on `<html>`. A set page opened with `?kb=1` shows the numbers it reads. See the footgun [fixed elements sit under the iPhone keyboard](footguns/ios_keyboard_covers_fixed.md). Not yet confirmed on a real iPhone.
- The options under “More host controls” are all full-width buttons, including Cancel this set and Or add one player.
- There is no toggle from 900 px, without JavaScript, or for players.
- Code: `templates/web/_host_controls.html`, `static/js/dock.js`, the last block of `static/css/app.css`. `static/js/live.js` gives focus back to a redrawn control that carries `data-focus-key`. `static/js/counts.js` also writes the verdict to the bar.

## Archive and delete sessions and groups

- **Archive a session.** A host opens “Manage this session” on the session page and confirms. Allowed when no set is a draft, open, in play or counting up. The confirmation lists transfers that are not marked paid.
- **An archived session** leaves the Sessions list and Your groups, and its results leave the stats, player records, “To settle” and the group rake total. Its pages stay readable by link with an “Archived” notice. No write is accepted. Hosts find it under “Archived sessions” at the bottom of the Sessions tab and restore it from its page; everything returns as it was.
- **Delete a session.** Offered only when no money record exists under it (a reversed buy-in is still a record) and no set is unfinished. It removes the session and its sets for good.
- **Archive a group.** Group settings → “Manage this group”. Refused while any set is unfinished. The group leaves Your groups for every member, every page of the group returns 404 and its invite links are refused. Hosts restore it from “Archived groups” on Your groups.
- **Delete a group.** Only when no session of the group holds a money record. The host types the group name. It removes the group, memberships, tables, presets, invites and empty sessions. User accounts stay.
- Money records are never removed by any of these. Each action writes an audit event; the events of a deleted session or group stay.
- Not possible: archiving or deleting a single set, purging an archived group, deleting a user account.

## Entry pages

- Log in, Sign up, “Sign-up needs an invite” and Join group share a centred frame led by the mark and the name. Signed-out pages have no site header.
- A person who arrives from a usable invite link sees “You’re invited to {group}” on Log in and Sign up. An invalid, expired, used-up or revoked link shows nothing. `accounts.signup.INVITERS` is filled by `groups.access.invite_group_name`, so `accounts` does not import `groups`.
- Sign up asks for a username, a password and the password again. The help is one short line each; the password rules are Django's four validators, unchanged. A broken rule is reported under Password.
- Password fields have a Show / Hide button when JavaScript runs (`static/js/password.js`).
- Join group shows the group name and the number of active players.
- Log in is `accounts.views.Login`, Django's `LoginView` with the invite name added to the context.

## Settle status of a session

- A closed session is Settled when every transfer has an active payment (or it has no transfer), Partly settled when some do, Unsettled when none do. Nothing is stored: `settlement.queries.settle_status` is the one rule.
- Group → Sessions → Past sessions shows the status badge on each row and the amount still to pay; the heading counts the sessions not settled. `settlement.queries.settle_states(night_ids)` reads any number of sessions in two queries.
- The session page shows the same status in its top bar and in its overview.
- Hosts and players see the same settlement facts. Hosts have Mark paid and Undo actions; player and archived views have no action column.
- Who pays whom cards adapt to their available width. Below 440px, payer and payee each have a full-width row; wider cards show them side by side. Chips align with the first name line. Amount, payment state and action have explicit grid positions, so a paid timestamp grows below the badge. Complete amounts and units stay on one line.

## Stakes forms

- New session, Set settings and the preset form group their fields: When and where, Game, Stakes, Rake per buy-in. Short fields sit in pairs. Field names, validation and what is saved are unchanged.
- Templates: `games/_game_fields.html`, `games/_stakes_fields.html`, `games/_rake_fields.html`, and `partials/field.html` for one field. Other forms still use `partials/form_fields.html`.
- Every form shares one field box in `app.css`; see the footgun on the iPhone date input.

## Entry flow (after the critique)

- A signed-out visitor to `/join/<token>/` with a usable invite is redirected to Sign up (`groups.views.accept_invite` is exempt from the login requirement). A bad link shows its reason at once with status 404.
- An account created from a usable invite joins the group in the same request: `accounts.signup.AFTER_SIGNUP` holds `groups.access.join_from_invite`, which calls `services.accept_invite`. If the invite stopped being usable in between, the account exists and the visitor lands on the invite page.
- An existing account still confirms on the Join page.
- Words: `accounts.forms.LoginForm` and `SignupForm.WORDS` replace Django's messages by error code. Validators are unchanged.
- Log in offers Sign up only when `accounts.signup.allowed` would open it.
- Two critique snapshots for these pages are in `.impeccable/critique/` (24 then 25 of 40).

## Installable app

- A web app manifest (`static/manifest.webmanifest`), PNG icons in `static/icons/` and iPhone meta tags let a phone add the site to its home screen and open it full-screen.
- `static/js/app.js`, on every page: the offline notice; no form is sent while the browser reports offline; a page that does not refresh itself reloads when the app returns after 30 seconds away, unless a field holds unsaved typing, a sheet is open, or the page was rendered from a POST; and the service worker registration.
- The service worker (`config/pwa.py`, served at `/sw.js`) does one thing: a navigation that fails for lack of a connection shows `/offline/`. It caches that page only. `SERVICE_WORKER=False` serves a worker that removes itself, and pages then also remove any worker and cache on the phone.
- Not built: offline viewing or recording, push notifications, an install prompt, splash images, an app-store app.

### Put PokerNights on your phone

- **iPhone:** open the site in Safari, tap Share, then Add to Home Screen.
- **Android:** open the site in Chrome, open the menu, then Install app or Add to Home screen.
- On an iPhone you log in once more inside the installed app; it does not share Safari's login.
- An invite link opened from a chat still opens in the browser, not in the installed app.

## Actions update in place

- On the set page and the session page, forms that return to the same page are sent in the background and the page is updated without a reload: buy-in and rebuy, cash-out, confirm and clear counts, set transitions, player actions, reversals, overrides, finalize, mark paid and undo. They carry `data-turbo="true"`; a button that submits a form from outside it (`form="counts-form"`) carries it too, because Turbo checks the pressed button. Since 2026-10-06 the server answers such a form with the updated page itself, so an action is one request, not a post followed by a fetch of the page.
- `static/js/turbo-setup.js` keeps navigation off for everything else, preserves text typed in a `data-keep` field that was not part of the sent form and any open `data-key` disclosure, raises `inplace:updated` and then the existing `live:updated`, and turns a failed send into `inplace:failed`.
- An answer that is not an update of the same page (another address, a 403 or 404) loads the ordinary way. A 5xx changes nothing and shows a failure message.
- `sheets.js` closes the sheet after a successful update and leaves the page's fresh form (with a new `request_id`) in place; after a refusal it keeps the sheet, the typed amount and the error, and takes the fresh `request_id`.
- `toasts.js` floats success messages, and after an in-place update floats errors too, because the page may be scrolled.
- Turbo's page cache is off on every page. Links and all other forms load a page as before; that is stage 4.
- Without JavaScript every form is a native form, unchanged.

## Screen changes without a reload

- Tapping a link swaps the screen without unloading the page: one request, no rebuild, no blank moment. Back and Forward fetch a fresh page and restore the scroll position.
- A link is fetched as the finger touches it.
- Forms that lead to another page (New session, close session, log in, log out, group settings) still load a page.
- A slow screen shows a thin brass line at the top after half a second.
- Without JavaScript every link is an ordinary link.

## Limits today

- The app records who owes what. It does not move money.
- The transfer list excludes rake already collected at buy-in. It assumes no earlier player payments. A player payment during the game cannot be recorded yet.
- A finalized set and a closed session cannot be reopened. Check the cash-outs before finalizing.
- No breaks: "Left" is the way to stop a player's time. The end time of a set cannot be edited.
- The session page does not refresh by itself; the set page does.
- No banker mode, no seating and no seasons. Stats have no minimum-session threshold, average result or ROI yet.
- No password reset by email. A host sends a reset link (see “Password reset link”). A site administrator, a person who hosts two or more groups, and the only host of a group still need a superuser in `/admin/`. No screen changes a password while logged in.
- On the public address, an account can be created only from a usable invite link; a superuser adds the first host of a group.

See the [roadmap](../roadmap/README.md).

## Active set design (slice 1)

- The Rack uses an indigo table field, warm dark ground, Archivo figures and player tokens with initials. Home, group, accounts, forms and log use the completed Rack compositions.
- The first phone viewport shows still in play, clock and blinds. Total bought in and cashed out are plain labelled rows; there is no split bar. The indigo field appears only while the set is in play; draft and open sets use the neutral lead panel. From 900 px, the field and host controls sit beside the player list.
- Each host row has written Buy-in or Rebuy and Cash out buttons at every width. Tap a player's name for playing time, money records and corrections. The next host action sits in an opaque phone dock. More host controls includes settings, cancellation and adding one player.
- Without JavaScript, each row has expandable forms for the same actions.
- A refused sheet submission reopens with typed amounts or reasons and the server's error. Pending buttons say “Sending…”. A changed server figure gets a temporary brass highlight; an unchanged refresh has none. Figures never count up.
- Live updates keep open sheets and their focused field intact. Count-up uses one inline form and preserves typed drafts during polling.
- Native dialogs support keyboard focus, Escape and focus return. Reduced motion disables movement. Chip colour comes from join order and repeats after ten; initials remain visible.

## End-of-set design (slice 2)

The layout and several details below changed on 2026-10-05; “Count-up, review and finalize” at the end of this page describes the screens as built. What still holds from this list: the accounting gates, frozen results, the once-per-set books-balance rule, two columns from 900 px and JavaScript-free forms.

- Count-up uses the neutral lead panel and shows ready plus finally cashed-out players out of all players with buy-ins. Earlier partial cash-outs do not complete a player. Total bought in and recorded cash-outs have separate labels.
- Every eligible host count field stays inline. A confirmed count is written above the draft field. Count confirmation and recording cash-outs remain separate actions. Players see statuses and confirmed counts without host inputs.
- The host dock links to the batch review when counts are ready, offers finalization only when the books balance, and exposes the next-step explanation. Resume play and cancellation remain under More host controls.
- Batch review shows the confirmed amount to record, this batch's total, the amount already cashed out and the prospective total after confirmation. It makes no payment and does not finalize.
- The books-balance double rule appears only when the existing accounting gate passes, including disclosed overrides. It animates once per set per browser; with Motion the rule draws and then the words rise. Reduced motion leaves it static.
- Final set results use frozen snapshots, with Final tags, signed amounts, directional icons and time played. The viewer's result is prominent. Who pays whom stays on the session page.
- Count-up, review and finalized pages use two columns from 900 px. On phones, counts stay in one column; the balance check sits above the count list. Waiting for counts is a neutral notice. When every player is cashed out and the books still differ, the panel leads with the exact signed amount and the next step. Long names wrap. JavaScript-free forms remain usable.


## Session and settle-up design (slice 3)

- Open sessions lead with the current set action and show Results so far over finalized sets. Host close controls explain unfinished sets. Closed sessions lead with Still to pay and settled/partly settled/unsettled status.
- Still to pay sums unpaid transfers. The progress bar measures paid amounts against all transfer amounts; the paid transfer count is labelled separately. A fully paid session says Settled in words instead of ₱0. With no transfers, the page says Nobody owes anything and shows no bar. Paying or undoing a transfer does not change frozen poker results.
- Each transfer is a card with payer, payee, tokens, amount and Paid / Not paid. Only hosts see Mark paid and Undo. Payment records retain undone rows and name the recorder. Session results use signed figures, directional icons and a Final tag only after closing.
- Initial tokens use session standings' first-appearance order, keyed by member. They may have different colours from an individual set. Full names stay visible.
- The closing recap opens automatically once per session, signed-in viewer and browser. View session recap reopens it manually. Close, backdrop tap and Escape dismiss it; Tab stays in the modal, and focus returns to the trigger. Reduced motion is static. Storage refusal skips automatic opening; manual access remains. Without JavaScript, the recap is inline and native payment/close/next-set forms still work.
- Recap Recorded play time sums known finalized-set durations, says Not recorded if none are known, and marks a partial sum. It excludes canceled sets. Total bought in across finalized sets sums frozen buy-in snapshots, so money bought in again in another set is counted again. Top session result names all tied winners; break-even sessions say Everyone broke even. Your session result is omitted for a non-playing viewer.
- The page is one column on phones and 400 px / flexible columns from 900 px. Long settlement amounts use a smaller fixed type size to preserve the whole numeric value on one line. This page still requires reload to see another client's payment changes.

The [parent plan](../plan/1791046015_visual_redesign.md) records remaining slice 4; [slice 2](../plan/1791050738_redesign_slice_2.md) and [slice 3](../plan/1791053204_redesign_slice_3.md) record verification.


## Remaining screen design (slice 4)

- Home shows group navigation and roles, then group creation. Empty home explains how to create or join a group.
- Group shows current sessions first, with New session above the list for hosts. Past sessions follow. Tables, presets, roster and invitations form a management rail from 900 px and follow sessions on phones.
- Roster names stay alphabetic. Initial tokens use member ID and the existing palette; colour is not a cross-view identity guarantee. Host tools use native disclosures.
- Failed group creation, table creation, roster add and rename keep editable values, show a local error and open the failed disclosure. Success uses the existing redirect. Passwords stay blank on refused account submissions.
- Account, invitation, session, preset, settings and picker pages share a narrow form frame. The picker still supports search and native all-or-nothing submission.
- The set log groups complete records by category, with exact amounts, actors, times and reasons. Reversed and voided rows stay visible. Frozen results show signed values and Final labels. Native section links aid navigation.
- Canceled sets show their reason, retained roster and log link, with no final result or money action.


## Your groups home

- The first page lists each group with its players, one status band and one next action for the viewer: **Open the table** for a set in play, **Open set N** for a draft, open or counting set, **Go to the session** when every set is finished, and **New session** or **Add a table** for a host in a quiet group. A player in a quiet group gets no button.
- A set in play shows players at the table and the timer on the blue felt band. Money still in play is not shown here; the page does not refresh by itself.
- **To settle** lists the viewer's unpaid transfers from closed sessions ("You owe Miguel ₱425", "Jerome owes you ₱1,375"), three at most, each linking to its session. Nobody sees another member's debts here.
- **Your record** shows profit or loss, sessions and wins per unit, by the same rules as Stats. **Last session** shows the viewer's result in the latest closed session, or "You did not play".
- Groups with a set in play come first, then groups with an open session, then by name. Drafts stay hidden from players.
- Create a group is a closed section under the groups. A person with no group gets a first-group screen.

- **Since 2026-10-05 each group is a card** with one settings button (a gear, top right) in place of the Sessions, Stats and Group settings links; the name still opens the group. The card shows who, now and you in that order; the viewer's record and last result are large figures side by side; "New group" is a button after the last card. Template `templates/web/_group_card.html`; check `web/tests/browser/home.mjs` with `seed_home.py`. Details in DESIGN.md.

## Group page, stats and branding (UI evolution)

- The group page has tabs on the one group address: **Sessions** (default), **Stats** and **Group settings** (`?view=stats`, `?view=settings`). An unknown `view` shows Sessions.
- Sessions lists current and past sessions. With none in progress, a neutral card gives one next action for the viewer: New session, Add a table (host without tables), or a note that a host starts it.
- Group settings holds players, invite links, tables, presets and the group rake account. Each management action returns to its own section. Players read the same lists without host forms.
- Stats appears once the group has a closed session. It ranks players by profit or loss, with sessions played and win rate, for all time or one month, and for pesos or chips separately.
  - Only closed sessions count, using the current frozen results of their finalized sets. Canceled sets and open sessions are excluded.
  - A player's sets are added per session first. Several sets in one session count as one session.
  - Profit or loss is the result after rake. It is not the settle-up balance.
  - Win rate is profitable sessions divided by sessions played, rounded down. A break-even session is played, not won.
  - The month is the session's date. Players who left the group keep their history. There is no minimum number of sessions.
- Words: a **Session** is the whole gathering and its settle-up; a **Set** is one round of buy-ins, counting and results. Screens say Set settings, Set log, Join this set and Poker variant. "Pesos game" and "chips game" still name the unit.
- Branding: `static/branding/` has `logo-mark.svg` (a notched chip with a crescent), `logo-horizontal.svg`, `app-icon.svg` and `logo-mono.svg` for cream backgrounds. The header shows the mark beside the name; the mark is the favicon.

## Motion (stage 1 of the motion overhaul)

- Buttons sink under a finger and spring back. A sent control shows a running brass line until the answer arrives; an accepted one pulses once; a refusal nudges the field or message that explains it.
- Sheets rise from the bottom edge with a spring and can be closed mid-rise. Toasts arrive, stack without overlapping, and drop away when dismissed. The host dock opens with the same spring.
- Reduced motion, no JavaScript, or a Motion file that fails to load: the app works as before.
- Code: `static/js/motion.js`, `static/js/vendor/motion-14.0.0.js`, the "Motion system" block at the end of `static/css/app.css`. Check: `web/tests/browser/motion.mjs`.

## Motion between screens (stage 3 of the motion overhaul)

- A tapped link that goes deeper (Your groups → group → session → set → set log or a form) shifts the screen one way; a link that goes back shifts it the other way. A group's tabs shift their content sideways and slide the marker. The phone's own Back and Forward keep the plain cross-fade.
- The group's name and the session's table name travel from the card or row that was tapped to the next screen's heading, and back. Players' chips travel between a session's results and a set's rows. The top bar stays still.
- A movement lasts at most 260ms and a tap during it is followed.
- Reduced motion, no JavaScript, or a browser without the feature (an iPhone before iOS 18): screens change at once.
- Code: `static/js/turbo-setup.js` (direction, carried names, the transition itself), the last block of `static/css/app.css`, `data-depth` / `data-tab` / `data-carry` in the templates, `data-m` on chips. Check: `web/tests/browser/screens.mjs`. The table of movements is in DESIGN.md.

## Motion on the live set page (stage 2 of the motion overhaul)

- A change on the set page is shown as movement, whether you made it or another person did: a new player's row fades in and rises; rows slide to their place when a row above changes height; a new buy-in edge drops onto its stack; badges spring in; the brass mark fades out instead of vanishing; the "Still in play" underline draws; a new set state fades in; the books balancing draws its rule and then raises its words, once per set per browser.
- Figures show their accepted value from the first frame. Rows never reorder.
- Nothing moves on first sight of a set, while you type, in a hidden tab, under reduced motion, without JavaScript or if the Motion file does not load.
- Code: `static/js/flow.js`, `static/js/changes.js`, the last block of `static/css/app.css`. Check: `web/tests/browser/flow.mjs`. The events table is in DESIGN.md.
- Next stages (each with its own plan): the live set page, moving between screens, results and settle-up.

## In-app numpad (2026-10-05)

- **On a phone or tablet a typed number uses the app's own keys.** The phone's keyboard does not open for buy-in, rebuy and cash-out amounts, final counts, stakes, rake or seats. Text fields (names, reasons, notes) keep the phone's keyboard. On a computer nothing changes.
- **Twelve keys in fixed places:** 1 to 9, one key that depends on the field, 0 and delete. That key is a decimal point where a decimal is allowed (pesos, the rake percentage) and "00" where it is not (chips, seats). On the setup forms it follows the Unit choice. Holding delete clears the field.
- **A key that cannot give a valid number does nothing** and the field is marked for a moment: a second decimal point, a third decimal place, a digit past the largest amount.
- **In a buy-in or cash-out sheet** the keys are part of the sheet, between the amount and the action.
- **On a page with several number fields** (count-up, New session, Set settings, presets, New table) a panel rises from the bottom when a number field is tapped. It names the field and has **Next** and **Done**. During count-up it takes the host bar's place, shows the running total, and Next goes to the next player still to count.
- **It fails safe.** The field stays a real field and the form sends the same value. The phone's keyboard is switched off only once the keys exist. If the script is missing or fails, or with the environment variable `NUMPAD=False`, every field uses the phone's keyboard as before.
- Script: `static/js/numpad.js`. A field opts in with `data-numpad="pesos|chips|percent|whole|amount"`; a form that wants the keys in a fixed place holds an empty `<div data-numpad-slot>`. [Plan](../plan/1791202390_host_gaps_numpad_count_up.md).

## Count-up, review and finalize (rework of 2026-10-05)

From the [critique](../study/1791201933_host_gaps_numpad_count_up.md) of the end-of-set flow.

- **Count-up leads with the players.** On a phone the overview is the title and one progress line; the players' count fields follow at once. Set totals and the balance check are below the list. Once every player is cashed out, the balance check moves directly under the overview, so a discrepancy is the first thing on the screen.
- **One running total.** For the host it is in the bottom bar on a phone (open or folded) and with the main button on a computer. A player sees one read-only total under Set totals.
- **A row is a name, a state and one field.** A confirmed count shows in its field in the quieter colour. Rows have no button of their own. Buy-in and time details are in Details.
- **One main button, by state:** "Confirm N counts" while counts are typed; "Cash out counted players (N)" when counts are confirmed; "Finalize results" when everyone is cashed out and the books balance; "See the ₱100 difference" when they do not. With nothing typed and nobody counted there is no button, only the line that says what to do. "Confirm all counts" at the end of the list remains for a browser without scripts.
- **The verdict has a tone and a mark:** brass with a warning mark for missing or extra once every count is in, green with a tick for a match, plain while counting. With an override it reads "Off by ₱100, covered by an override."
- **Typed counts are kept for the tab** until they are confirmed, so leaving the page does not lose them.
- **The review says where the books will stand,** directly above its button: they balance; they are ₱50 short or over; or some players are still to count.
- **Finalize asks once.** The button opens a sheet with the players, total bought in, total cashed out and the verdict, and one button "Finalize set N". "Not yet" has the focus. Without scripts the same content is a disclosure.
- **Messages sit above the bottom bar** on a set page, never on it.
- **The final page leads with its proof:** "6 players · ₱9,500 in · ₱9,500 out" and "The books balance." The cash-out total is labelled "Total cashed out". Rake rows show only when rake was collected. An even result reads "Even". A final set shows no Live status.
- **Host controls are evenly spaced:** 8px between neighbouring controls at every width.


On count confirmation, a visible typed field keeps its position when the accepted status adds a line. Other forms' drafts and open Details remain intact. See [the scroll footgun](footguns/count_status_moves_the_field.md).

## Feedback on a touch (2026-10-06)

- A link that changes the screen (a session row, a set link, a group name, a row on a group card, a back link) lightens the moment it is touched and stays so until the next screen is drawn. A link that is a button shows the busy line. A group's tabs do not light: the marker sliding to the tab is their answer.
- A changed player or count row is marked by a brass box inside the row. "Rebuy added" or "Updated" appears in the line under the player's name. Neither covers another row, a name, an amount or a button.

## Measuring on a phone (2026-10-06)

- Add `?perf=1` to any address. A small readout stays at the top of that tab and adds one line per tap: `wait` (tap to the server's answer), `draw`, `move` (until everything has stopped), the total, then `server` (the whole request), `db` (time in queries, with their count), `open` (time to open a database connection) and `late` (frames longer than 25 ms, of all frames, with the longest).
- A screen that was fetched when the finger touched its link reads `wait 0 (fetched ahead)`.
- `?perf=0` removes it. It lasts for the tab only and nothing runs without it.

## Password reset link (2026-10-06)

- **A host creates it.** Group settings → Players → “Manage {name}” → **Create password reset link**, for a member with a login. The link is shown once in the Players section and is sent by the host; the app sends nothing and stores only the link's hash.
- **It works once and for 24 hours.** Creating another cancels the earlier one. While one is live the member's Manage block says “Reset link active until …” with **Cancel link**. Any host of a group the person is in sees and can cancel it.
- **Refused for:** yourself; a roster player without a login; a site administrator (staff or superuser); a person who hosts another group. The last two keep a host from reaching the admin or another group's host powers by taking over an account.
- **The person opens it** (`/accounts/reset/<token>/`, signed out or not): the page names their username and asks for a new password twice, with Sign up's rules and wording. Saving logs them in on Your groups and signs every other device out. Opening the link without saving changes nothing, so a chat app's preview cannot spend it.
- **A link that is used, cancelled, expired or unknown** answers 404 with the reason and “Ask a host of your group for a new one.”
- **What a host can still do:** open the link themselves and log in as one of their own players. The audit log records who created the link (`password_reset.issued`), a cancel (`password_reset.cancelled`) and the use (`password.reset`).
- **Switch:** `RESET_LINKS=False` hides the action, refuses every link and returns Log in and Sign up to the “no reset yet” wording.
- Code: `accounts/services.py` (the link's life and the password change), `groups/services.py` (`create_password_reset`, `cancel_password_reset`: who may ask), `accounts/views.py` (`password_reset`), `templates/accounts/reset.html`. Check: `web/tests/browser/reset.mjs`. [Plan](../plan/1791263947_host_issued_password_reset.md).

## Copy button on a new link (2026-10-06)

- A new invite link and a new password reset link each have a **Copy** button inside the right edge of their read-only field. A tap copies the whole address; the button reads **Copied** for two seconds once the browser has confirmed it.
- If the browser refuses, or has no clipboard (an http address), nothing says Copied: the address is selected in the field and a line under it says "Could not copy. The link is selected: copy it from the menu."
- Without JavaScript the button is hidden and the field is selected by hand, as before.
- Code: `static/js/copy.js` (a button with `data-copy="<field id>"` and a status line with `data-copy-status`), `templates/web/_copy_field.html`. Check: `web/tests/browser/copy.mjs`. [Plan](../plan/1791265490_copy_link_button.md).

## Player rebuys and player-entered counts (2026-10-06)

**A player's own rebuy**

- A player with a login who is at the table and already has a buy-in sees **Rebuy** on their own row, and the host's sheet behind it. The rebuy is recorded at once with the set's limits and rake; the log names the player as the recorder.
- Only for themselves. The first buy-in, a player who has left, a player with a final cash-out, and every player without a login stay with the host. Only a host reverses.
- Every phone on the set shows it within about 5 seconds, with the brass mark and "Rebuy added".

**No doubled rebuy**

- Every buy-in form carries `seen_count`: how many buy-ins the page showed for that player. If that is no longer true, nothing is recorded and the sender reads "maria already has a new rebuy (₱1,000, recorded by maria at 21:40). Nothing was added. Check, then try again if this is another one." This holds for the host's sheet too. A sheet left open through a live update is refused once, takes the fresh number, and a second tap records.

**A player's own final count**

- While a set is counting up, a player with a buy-in who is not cashed out has a field **Your count** and **Send to host** on their own row. 0 is valid. They can change it until the host has confirmed a count for them.
- An entered number is a statement, not a count. The player stays "awaiting": it is in no total, no balance and no cash-out. Every member sees the badge **Entered** and "₱1,450, not confirmed yet" on that row.
- The host's field for that player stays empty, shows the number as its hint, and says "maria entered ₱1,450. Leave the field empty to accept it, or type another number." The running total counts it as a preview, and the main button reads "Confirm N counts" with entered and typed counts together. A typed number wins.
- The host confirms the number on their screen or nothing: if the player changed it in between, nothing is saved and the page shows the new number.
- After the confirmation the player reads "The host confirmed your count." or "The host confirmed ₱1,400. You entered ₱1,500."
- Clearing a count, or resuming play, retires the player's statement; they can enter again.

**Unchanged:** confirming and clearing counts, cash-outs, the balance check, overrides, finalizing and settle-up are host-only.

- **Switch:** `PLAYER_ENTRIES=False` removes both player actions and ignores numbers already sent.
- Code: `ledger.services.record_buy_in` (the player path and `seen_count`), `enter_count`, `confirm_counts(entries=…)`; `ledger.models.CountEntry` and `FinalCount.entry`; `PlayerLine.entered`; `templates/web/_players.html`, `_players_count.html`; `static/js/counts.js`. Check: `web/tests/browser/player_entries.mjs`. [Plan](../plan/1791266619_player_rebuys_and_counts.md).

## Roster management (2026-10-09)

Group settings → Players. [Plan](../plan/1791525658_roster_management.md).

- **Rows.** Each player has the token, the name, the Host and No login badges and one line: "12 sessions · last played Oct 1" or "No sessions yet". A session counts as in Stats (closed, not archived, with a counted result), once whatever its unit. Every member sees it. Names are in order whatever their capitals.
- **Your own name.** Your row has "Change your name", for a host and a player. It is the name in this group; the username you log in with does not change.
- **Manage a player (hosts).** One form saves the name and a contact note of up to 120 characters. Only hosts see the note, and its text is not written to the audit log. Make host, Make player and the reset link are below it, and Remove from group sits apart under a rule.
- **Removing.** Remove from group opens a page that asks first. It says what happens, lists the player's unpaid transfers under "Still to pay" and has "Remove {name}" and "Keep {name}". Opening the page removes nobody. Unpaid transfers do not stop a removal and stay on their session pages.
- **Refused removals.** A player at the table of a set that is not finished (setup, open, in play or counting up) cannot be removed: the page names the set and links to it. The only host cannot be removed. Withdrawn and Left players, and finished or canceled sets, do not block.
- **Removed players.** A closed list for hosts at the end of the panel, with Bring back. The member row is the same one, so past results and Stats are unchanged. A returning player is a player, also a former host. A person with a login can open the group again at once. If another active player took the name, they return as "{name} (2)" and the message says so.
- **A removed name is not added again.** Adding a name that a removed player has is refused and points to Removed players, in Group settings and on a set's Add players page. A second row would split that person's history, and nothing merges members.
- **A removed player who Left a set** is not brought back to that table until a host brings them back to the group.
- **Several names.** "Add players without a login" takes one name per line, up to 30. Everyone is added, or nobody is; blank lines are skipped. A refusal names every problem at once (already in the group, typed twice, removed, too long) and keeps the text. The box counts the names while they are typed.
- **Said on the page.** Rows that were just added or brought back carry the brass mark for three seconds and rise into place; after a removal the Removed players line is marked. An opened disclosure eases in. Under reduced motion the mark shows and nothing moves.
- **Switch:** `ROSTER_TOOLS=False` returns the section to one-name add, rename and remove, and the new services refuse. The removal page and its checks stay on.
- Code: `groups/services.py` (`remove_member`, `restore_member`, `rename_self`, `edit_member`, `add_roster_players`, `REMOVE_GUARDS`), `games.services.guard_member_removal`, `settlement.queries.roster_activity`, `settlement.views.member_remove`, `static/js/roster.js`.

## Claim links (2026-10-09)

A player who was only a name on the roster gets their own login and keeps their history. [Plan](../plan/1791527506_claim_links.md).

- **The host creates it.** Group settings → Players → "Manage {name}" on a player without a login has **Create claim link**. The link is shown once with a Copy button, with what it does: whoever opens it becomes that player in this group. It works once and lasts 7 days. While one is live the block says until when and offers **Cancel link**; a new link cancels the earlier one.
- **A newcomer** who opens it goes to Sign up, which names the group, and is the player as soon as the account exists.
- **A person with an account** gets one page that asks: the player's token, "Join {group} as {name}", the account they are logged in as, a **Claim {name}** button, "Not now" and a way to log out of the wrong account. Opening the link changes nothing.
- **Already in the group with nothing recorded:** the page says that entry is replaced, and the claim deletes it. If it was a host, the claimed player is a host.
- **Already in the group with games recorded:** refused: "Two records cannot be joined yet." A person who was removed with games recorded is told to ask a host to bring them back.
- **What a claim changes:** only who can log in as that member. The member row is the same; no result, transfer, payment, seat or count is touched. The player keeps the roster name and can change it. From then on their own rebuys and counts are accepted.
- **It cannot be undone in the app.** For a wrong claim, remove that player and add the right person.
- **A dead link** (unknown, cancelled, used, expired, the player removed, the group archived) shows "This claim link doesn't work" with the reason. The account that used a link is sent to the group when it opens the link again.
- **Switch:** `CLAIM_LINKS=False` hides the action, refuses new links and makes every link not valid.
- Code: `groups.models.ClaimLink`, `groups/services.py` (`create_claim_link`, `cancel_claim_link`, `claim_preview`, `claim_member`), `groups/access.py` (the sign-up hooks), `groups/views.py` (`claim`), `templates/groups/claim.html`.

## Stats board and player pages (2026-10-09)

[Plan](../plan/1791528961_stats_revamp.md). Everything is worked out when read, from the frozen results of closed, unarchived sessions, one unit at a time.

- **Your summary** leads the Stats tab: your profit or loss for the unit and period, your place ("3rd of 9", or "Not ranked yet: 1 of 3 sessions"), your last result, and **Your stats**.
- **Periods:** All time, This year, Last 3 months (this calendar month and the two before), and one month picked from a list of the months that have a closed session.
- **Order:** Profit, Average, Return, Per hour (offered only when the period has recorded time) and Sessions. The figure at the right of a row follows the order; when it is not Profit, the profit or loss sits small beneath.
- **Ranked and not ranked.** A player needs 3 sessions in All time and This year, 2 in Last 3 months and 1 in a month. Others are listed under "Not ranked yet" without a place.
- **Movement.** Beside a place, "up 2", "down 1" or "New", against the same board one period earlier; All time compares with the board before the latest session date. No mark when nothing changed or there is no earlier board.
- **A removed player** stays, with "Left the group".
- **A player's page** (`g/<group>/players/<member>/`), open to every member of the group: the lead figure and rank; the **Running profit** line with a zero line and, beneath it on the same positions, a bar for **each session**; eight tiles (average per session, return on buy-ins, per hour, win rate, rebuys per session, total bought in, rake paid, time at the table); best and worst night, current run and longest winning run; and the last ten sessions with "Show all".
- **Reading the chart.** A touch, a pointer or the arrow keys pick a session: a line, a dot and a ring mark it, and the line under the chart says its date, table, result and running total. The chart needs three sessions; a longer record draws its latest 60.
- **How figures are worked out.** Average and per hour round toward zero to the centavo or chip; return and win rate to the whole percent. Per hour uses only sessions with recorded time and says how many. Rebuys are buy-ins beyond the first in each set. A run is sessions in a row with a profit, or with a loss; a break-even session ends it. Rake is already inside the profit or loss.
- **Changing period, unit or order** stays on the screen where it was scrolled, moves the chosen pill and the rows to their new places, and does not add a step to the Back button.
- **Switch:** `STATS_PAGES=False` returns the tab to the single ranked list and makes player pages not found.
- Code: `settlement/stats.py` (the figures), `web/charts.py` (the geometry), `web/stats.py` (what the pages show), `templates/web/_group_stats.html`, `player.html`, `_running_chart.html`, `static/js/stats.js`.

## Numpad motion (2026-10-09)

The app's number keys answer a tap ([plan](../plan/1791533332_numpad_motion.md)): a hit key lights and the amount pulses once; Delete nudges the field; holding Delete shows a fill across the key for the half second before the field clears, and letting go early clears nothing; a refused key shakes and turns its border red along with the field; the keys rise into a Buy-in, Rebuy or Cash out sheet; and Next in the bottom panel brings the next field's name in. Typing is as fast as before, digits appear whole, and nothing moves under reduced motion. Code: `static/js/numpad.js` (`go`, `lit`, `tick`, `rise`, `held`).
