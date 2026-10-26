# Features

What the app does today (Stage 1). Items that are planned but not built are listed at the end.

## Accounts and groups

- Sign up, log in, log out.
- Your profile (since 2026-10-17): see "Profile" below.
- Create a group. The creator is a host.
- A host creates an invite link (valid 7 days, 20 uses, revocable). A signed-in person who opens it becomes a player. Since 2026-10-16 every active link can be copied or shared again from Group settings (see "Invite links shown again").
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
- After play of a set has ended, the host taps **Play set N** under “What next?” on the final set page or the session page. The new set has the same table and settings and the players who were still at the table. The host can add or remove players before starting it.
- Who pays whom is worked out **once per session**: the host taps **Settle up** under “What next?”, then **Close session and settle up** in its sheet, when every set is finalized or canceled. The list nets each player's results over all sets.
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
11. **Close the session.** The app lists who pays whom with the minimum number of transfers, after it subtracts the payments made at the table. The host marks each transfer paid, and can undo it. The session shows unsettled, partly settled or settled.
12. **Set log.** Each member can read the players, settings, each buy-in, reversal and cash-out, overrides, results, and who did what and when. Transfers and payment records are on the linked session page.

A game without accepted buy-ins can be canceled with a reason. A canceled game does not count.

## Session setup (polish of 2026-10-13)

- New session: "Start from a preset" is a group. `static/js/setup.js` fills Poker variant, Unit and the stakes from the option's `data-fill` (built in `games.views.session_new`) and sets `preset_id`; Location, Date and Table are kept. Without the script, "Use" reloads the page with `?preset=`.
- Rake: only the chosen rule's amount field is drawn, by CSS on the checked choice (`.rake-settings:has(...)` in `app.css`). Both fields are always posted; `RakeFields.clean` reads the chosen one.
- Draft set: the Stakes and rake step's button reads "Change" (its accessible name still says "Choose rake before buy-ins" while rake can be chosen). Its line is three `.fact` spans. A host's empty Players section has no sentence.
- Add players: the roster form comes first. The new-player form is still the page's first `form.form-section`, which the browser checks rely on.
- "More host controls" flies out (`fly()` in `static/js/dock.js`): see DESIGN.md. It is skipped under reduced motion and while the dock slides.
- Browser check: `session_setup.mjs` with `seed_setup.py` (see `web/tests/browser/README.md`).

## Add players in one send (2026-10-14)

- `games.services.add_players(session_id, actor, member_ids, lines, request_id)`: ticks plus new names, one transaction, one `ParticipantBatch`, all or nobody. The typed names are checked by `groups.services.new_name_problems` (shared with Group settings' several-names box), with "Already at the table" named apart and "Tick them in the list instead." after names on the roster. A refusal about the names is a `NamesRefused`, so the page marks the box. Seats are counted for ticks and names together before any roster player is made.
- `games.views.participants_add` reads `member_id` and `names` (a page drawn before this sends one `name`, which still works). The page carries `data-known` (roster names and ids, names at the table, removed names) for `static/js/pick.js`'s preview; the server checks again.
- On success the session holds `players_arrived` for one view of the set page; `_player_row.html` marks those rows `data-arrived` and `flow.js` gives them the mark and the rise. Polls never carry it.
- `add_new_player` and `add_participants` stay for their other callers and the race tests.
- Browser check: `new_names.mjs` with `seed_new_names.py`.

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
- **Rename a group.** Group settings → “Manage this group” → “Rename group”. Hosts only. The name is 1 to 60 characters; spaces are tidied. The same name writes nothing. An archived group is not renamed. The audit log keeps the old and the new name (`group.renamed`). Code: `groups.services.rename_group`.
- **Archive a group.** Group settings → “Manage this group”. Refused while any set is unfinished. The group leaves Your groups for every member, every page of the group returns 404 and its invite links are refused. Hosts restore it from “Archived groups” on Your groups.
- **Delete a group.** Only when no session of the group holds a money record. The host types the group name. It removes the group, memberships, tables, presets, invites and empty sessions. User accounts stay.
- Money records are never removed by any of these. Each action writes an audit event; the events of a deleted session or group stay.
- Not possible: archiving or deleting a single set, purging an archived group, deleting a user account.

## Entry pages

- Log in, Sign up, “Sign-up needs an invite” and Join group share a centred frame led by the mark and the name. Signed-out pages have no site header.
- A person who arrives from a usable invite link sees “You’re invited to {group}” on Log in. Sign up is headed “Join {group}”, with “{inviter} invited you · N players” under it. The inviter is named only while still an active member of the group; N counts the group's active members, with or without a login. An invalid, expired, used-up or revoked link shows nothing. `accounts.signup.INVITERS` is filled by `groups.access.invite_group_name` (an `accounts.signup.Invitation`) and `claim_group_name` (a group name only), so `accounts` does not import `groups`.
- Log in shows no description. “Forgot your password? Ask a host of your group for a reset link.” is always under the button.
- Sign up has “Keeps the books for your home poker game. It never moves money.” under the heading. It asks for a username and one password; Set a new password also asks once. The profile's change-password form keeps Repeat password (`accounts.forms.PasswordPairForm`). The password rules are Django's four validators, unchanged. A broken rule is reported under Password.
- Under the new password, “At least 8 characters” and “Not only digits” tick while the person types; a note says the other two rules are checked on sending. Sign up has no reset note under the password while reset links are on; Log in says where a reset comes from.
- The username hint and its error name the characters Django accepts: letters, numbers and `@ . + - _`, with no spaces.
- An invited (or claim-link) Sign up's button reads “Create account and join”. `static/js/password.js` does the ticks and announces each change in a polite live region. Without JavaScript the two lines and the note show, unticked. The server decides; a tick never lets through what it refuses.
- A refused field's error is directly under the field, before its help.
- Password fields have a Show / Hide button when JavaScript runs (`static/js/password.js`).
- Join group shows the group name and the number of active players.
- Log in is `accounts.views.Login`, Django's `LoginView` with the invite name added to the context.

## Paid at the table

[ADR 0002](../adr/0002-payments-at-the-table.md); [plan](../plan/1793020848_payments_before_close.md).

- While a session is open, the host records money that one player handed another at the table: who paid, who received, the amount. The session page has a “Paid at the table” section with **Record a payment** (a sheet; a plain page without JavaScript).
- On the set page, a left player's details offer **Paid at the table?** to the host. It opens the form with that player and their set figure filled in: a winner is the payee, a loser the payer. After recording, the host returns to the set.
- Only players with a standing buy-in in a set of the session can be named. The two players must differ. The amount is more than 0, in the game's unit.
- The host undoes a payment with a reason. The row stays, struck, with the reason. Nothing changes once the session is closed; reopen it first.
- Every member sees the list. A player's own payment also shows on the felt: “You paid Ana ₱300 at the table.”
- Closing subtracts each standing table payment from what is still owed, then works out who pays whom. Results and stats do not change. An overpayment comes back in the list. Closing refuses a payment that names someone with no result (for example after their buy-in was reversed).
- A closed session names these payments in “How this is worked out”. Payment records say “At the table” or “Marked paid”.
- A table payment does not count as a paid mark and does not block reopening. Closing again uses it again.

## Settle status of a session

- A closed session is Settled when every transfer has an active payment (or it has no transfer), Partly settled when some do, Unsettled when none do. Nothing is stored: `settlement.queries.settle_status` is the one rule.
- Group → Sessions → Past sessions states the status in words on each row: "Settled" with a check, "₱500 still to pay", or "Partly paid, ₱200 still to pay". The heading counts the sessions not settled. `settlement.queries.settle_states(night_ids)` reads any number of sessions in two queries.
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
- Launch screen (2026-10-14): opening the installed app shows the front door's hero, the stacked chip and "PokerNights" on Ground, until the first page paints. On an iPhone, `base.html` names one image per screen size (`apple-touch-startup-image`, sizes in `config.pwa.SPLASH_SIZES`); a phone with no exact match keeps a blank launch. An iPhone reads the image when the app is added to the home screen, so an app added earlier keeps its blank launch until it is removed and added again. Android draws its own launch from the manifest's background and its `any` icons, which since then are the chip on a clear ground (`app-any-192.png`, `app-any-512.png`); the maskable icon keeps its square. The source is `doc/showcase/splash.html`, rendered by `web/tests/browser/make_splash.mjs`. [Plan](../plan/1791953083_launch_splash.md).
- Not built: offline viewing or recording, push notifications other than table alerts (2026-10-15, below), an iPad or landscape launch screen, an app-store app. The install suggestion is described under “Home screen suggestion and Join with a link”.

### Put PokerNights on your phone

- **iPhone:** open the site in Safari, tap Share, then Add to Home Screen.
- **Android:** open the site in Chrome, open the menu, then Install app or Add to Home screen.
- On an iPhone you log in once more inside the installed app; it does not share Safari's login.
- On an iPhone an invite link opened from a chat still opens in the browser; inside the installed app, use Join with a link on Your groups. On Android an installed app takes links to the site, unless the chat app opens them in its own browser.

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
- The transfer list excludes rake already collected at buy-in. It subtracts the payments made at the table before closing (see “Paid at the table”).
- A reopened session cannot count payments already made toward its new transfer list: paid marks are removed first. See “Reopen a set or a session”.
- No breaks: "Left" is the way to stop a player's time. The end time of a set cannot be edited.
- A group's Stats and Group settings tabs do not refresh by themselves; Your groups, the Sessions tab, the session page and the set page do.
- No banker mode and no seasons. Seating is the optional seat draw (see “Seat draw”); the app does not follow the dealer button hand by hand. Stats have no minimum-session threshold, average result or ROI yet.
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
- The host dock links to the batch review when counts are ready, offers finalization only when the books balance, and shows a hint under the button only when the hint adds to the button's words. Resume play and cancellation remain under More host controls.
- Batch review shows “After this batch” against “Bought in” (and collected rake), the table of confirmed amounts with this batch's total, and the verdict above **Cash out N players**. It makes no payment and does not finalize. “Still to count” shows only when somebody is left.
- The books-balance double rule appears only when the existing accounting gate passes, including disclosed overrides. It animates once per set per browser; with Motion the rule draws and then the words rise. Reduced motion leaves it static.
- Final set results use frozen snapshots, with signed amounts, directional icons and one line of facts per player: in, rebuys, out, rake, override, time played. The viewer's result is prominent. Who pays whom stays on the session page.
- Count-up, review and finalized pages use two columns from 900 px. On phones, counts stay in one column; the balance check sits above the count list. Waiting for counts is a neutral notice. When every player is cashed out and the books still differ, the panel leads with the exact signed amount and the next step. Long names wrap. JavaScript-free forms remain usable.


## Session and settle-up design (slice 3)

- Open sessions lead with the current set action and show Results so far over finalized sets. Host close controls explain unfinished sets. Closed sessions lead with Still to pay and settled/partly settled/unsettled status.
- Still to pay sums unpaid transfers. The progress bar measures paid amounts against all transfer amounts; the paid transfer count is labelled separately. A fully paid session says Settled in words instead of ₱0. With no transfers, the page says Nobody owes anything and shows no bar. Paying or undoing a transfer does not change frozen poker results.
- Each transfer is a card with payer, payee, tokens, amount and Paid / Not paid. Only hosts see Mark paid and Undo. Payment records retain undone rows and name the recorder. Session results use signed figures, directional icons and a Final tag only after closing.
- Initial tokens use session standings' first-appearance order, keyed by member. They may have different colours from an individual set. Full names stay visible.
- The closing recap opens automatically once per session, signed-in viewer and browser. View session recap reopens it manually. It opens at its top with focus on Close (the source is marked `data-sheet-reads`; without that the focus would go to its only button, "Share results", its last line, and the browser would scroll there). A sheet reached from another sheet also starts at its top. Close, backdrop tap and Escape dismiss it; Tab stays in the modal, and focus returns to the trigger. Reduced motion is static. Storage refusal skips automatic opening; manual access remains. Without JavaScript, the recap is inline and native payment/close/next-set forms still work.
- Recap Recorded play time sums known finalized-set durations, says Not recorded if none are known, and marks a partial sum. It excludes canceled sets. Total bought in across finalized sets sums frozen buy-in snapshots, so money bought in again in another set is counted again. Top session result names all tied winners; break-even sessions say Everyone broke even.
- The recap has five sections ([plan](../plan/1791625392_session_recap_details.md)): the top result with the session's facts (total bought in, rake if any, players, finalized sets, number of buy-ins, play time); Your night, for a viewer who played (result, bought in, cashed out, buy-ins, time, the result of each set when there are several, and their transfers); Everyone's results, ranked best first with ties sharing a place and losses included; Highlights; and Set by set (players, bought in, time and who finished ahead, with a link to the set).
- Highlights are Most buy-ins (left out when every player bought in equally often), Biggest win in one set (left out with one finalized set or no winner) and Longest at the table (left out unless at least two players have recorded, unequal times). Ties name everyone. None states a loss, and the recap shows no percentage.
- "Cashed out" in the recap includes a player's share of a host override. Results are after rake. Canceled sets and superseded finalizations count nowhere.
- The page is one column on phones and 400 px / flexible columns from 900 px. Long settlement amounts use a smaller fixed type size to preserve the whole numeric value on one line. This page still requires reload to see another client's payment changes.

The [parent plan](../plan/1791046015_visual_redesign.md) records remaining slice 4; [slice 2](../plan/1791050738_redesign_slice_2.md) and [slice 3](../plan/1791053204_redesign_slice_3.md) record verification.


## Remaining screen design (slice 4)

- Home shows group navigation and roles, then group creation. Empty home explains how to create or join a group.
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
- Sessions shows the sessions in progress as table cards, then the past sessions (see "Sessions tab" below). With none in progress, a neutral card, "Nobody is playing", gives one next action for the viewer: New session, Add a table (host without tables), or a note that a host starts it.
- Group settings holds players, invite links, tables, presets and the group rake account. Each management action returns to its own section. Players read the same lists without host forms.
- Stats appears once the group has a closed session. It ranks players by profit or loss, with sessions played and win rate, for all time or one month, and for pesos or chips separately.
  - Only closed sessions count, using the current frozen results of their finalized sets. Canceled sets and open sessions are excluded.
  - A player's sets are added per session first. Several sets in one session count as one session.
  - Profit or loss is the result after rake. It is not the settle-up balance.
  - Win rate is profitable sessions divided by sessions played, rounded down. A break-even session is played, not won.
  - The month is the session's date. Players who left the group keep their history. There is no minimum number of sessions.
- Words: a **Session** is the whole gathering and its settle-up; a **Set** is one round of buy-ins, counting and results. Screens say Set settings, Set log, Join this set and Poker variant. "Pesos game" and "chips game" still name the unit.
- Branding: `static/branding/` has `logo-mark.svg` (a notched chip with a crescent), `logo-horizontal.svg`, `app-icon.svg` and `logo-mono.svg` for cream backgrounds. The header shows the mark beside the name; the mark is the favicon.
- Link preview: every page's head carries one card for chat apps (`templates/base.html`): the title PokerNights, the manifest's sentence, and `static/branding/link-preview.png` (1200 × 630). `config.pwa.flags` builds the picture's full address from the request. There is no `og:url`, because invite, reset and claim addresses contain a token; the card names no group. A signed-out fetch of an invite link is redirected to sign-up, which carries the same card. The picture's source is `doc/showcase/link-preview.html`; `doc/showcase/thumbnail.png` is a 1600 × 900 cover for use outside the app.

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

## The pot's figure rolls (2026-10-11)

- When "Still in play" changes on a set in play (a buy-in, a cash-out or a reversal, yours or another person's), the digits that changed roll to the new amount: upward for more, downward for less. The peso sign, commas and unchanged digits stay still.
- The amount added or taken out shows beside the label for 3 seconds: "+₱500", "−₱1,200.50", "+500 chips". Two changes in one update show their sum.
- The page's text is the accepted amount from the first frame. No other amount is shown and nothing counts.
- Nothing moves on first sight of a set, on a reload, in a hidden tab or if the Motion file does not load. Under reduced motion the figure changes at once and the amount added shows still.
- The "₱X bought in" line of a set that has not started is not part of it.
- Fail-safe: if the drawn digits cannot take exactly the plain figure's room, or the script would write the amount differently from the server, the figure is as it was before this feature. No switch.
- Code: `static/js/pot.js`, the `.pot-roll`, `.pot-cell` and `.pot-delta` rules in `static/css/app.css`. The script's formatter mirrors `ledger/money.py` and checks itself against the server's figure on every use. Check: `web/tests/browser/pot.mjs` with `seed_pot.py`.

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
- **The final page leads with its proof:** "6 players · ₱9,500 in · ₱9,500 out" (and "· ₱300 rake" when rake was collected) and "The books balance." No totals list repeats these figures. The date line ends with the set's time. An even result reads "Even". A final set shows no Live status.
- **Host controls are evenly spaced:** 8px between neighbouring controls at every width.

### What next? (2026-10-20)

[Plan](../plan/1792508082_end_of_set_words_and_next_step.md), [study](../study/1792508023_end_of_set_words_and_next_step.md).

- **Two equal choices.** On a final set page, a host sees “What next?” and two cards: **Play set N** (“Same players, new buy-ins.”) and **Settle up** (“End the session. See who pays whom.”). The open session page shows the same two cards. Neither is the default.
- **Play set N** starts the next set at once and opens it. No confirmation: an empty set can be cancelled.
- **Settle up** opens a sheet: “Close the session?”, three lines (how many sets are added up, who pays whom is listed, no set can start after this), the carry list when there is one, **Close session and settle up**, and **Not yet** with the focus. Without scripts the same content opens in place.
- **When the cards show.** Host only, while the session is open and no later set is open or in play. With a later set, the final page offers **Go to set N** instead. While another set is unfinished, Settle up is a disabled card: “Finish set N first.”, or “Cancel the set N draft first.” for a draft.
- **A player** reads “Who pays whom comes when the host settles up.” and **Go to the session**.
- **The session page** shows **Open set N** only for the latest set that is not finished. The rake row shows only when rake was collected. “Results so far” has a “Not final” badge.
- **On a phone** “Found a mistake?” and **Reopen set** follow the results, so the choice stands alone under the proof.
- **Motion.** The two cards rise 8 px and fade in once per set and browser, 60 ms apart, after finalizing. A press during the rise takes over. Reduced motion, a blocked Motion file and a reload show them at once.
- **Live.** A final set's poll version also carries the session's set states and status, so the choice changes when another set moves or the session closes.
- Code: `templates/web/_next_step.html`, `templates/web/_carry_pick.html`, `web.views.next_step`, `web.views.live_version`, `static/js/nextstep.js`, the “What next?” block at the end of `static/css/app.css`.


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

- A new invite link (and since 2026-10-16 every active one) and a new password reset link each have a **Copy** button inside the right edge of their read-only field. A tap copies the whole address; the button reads **Copied** for two seconds once the browser has confirmed it.
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
- The `STATS_PAGES` switch and the earlier single ranked list were removed on 2026-10-12, after the human accepted the board.
- Code: `settlement/stats.py` (the figures), `web/charts.py` (the geometry), `web/stats.py` (what the pages show), `templates/web/_group_stats.html`, `player.html`, `_running_chart.html`, `static/js/stats.js`.

## Numpad motion (2026-10-09)

The app's number keys answer a tap ([plan](../plan/1791533332_numpad_motion.md)): a hit key lights; holding Delete shows a fill across the key for the half second before the field clears, and letting go early clears nothing; a refused key shakes and turns its border red along with the field; the keys rise into a Buy-in, Rebuy or Cash out sheet; and Next in the bottom panel brings the next field's name in. Typing is as fast as before, and nothing moves under reduced motion. Code: `static/js/numpad.js` (`go`, `lit`, `rise`, `held`).

## Numpad digit motion (2026-10-09)

The pulse of the whole field was replaced ([plan](../plan/1791538209_numpad_digit_motion.md)). The field's box stays still: a typed digit fades and rises into its place, a deleted digit fades out, and in a right-aligned field the other digits glide to make room. While keys are tapped a drawn copy of the field's text lies over the field and the field's own glyphs are hidden; 300ms after the last key the copy is removed. The copy is not made when the text is wider than the field, under reduced motion or without Motion, and it is removed at once by a live or in-place update, by typing that is not from the keys, and when the keys leave the field. Code: `static/js/numpad.js` (`figure`, `place`, `measure`, `drop`); styles `.numpad-figure` and `input.is-figured` in `app.css`.

## Front door (2026-10-09)

- Every entry screen extends `templates/entry.html`: a `hero` block (the mark from `partials/mark.html`, through `partials/entry_head.html`) and a `sheet` block. Each screen still says itself whether the site header shows.
- `config/door.py` chooses the arrival. The context processor `door` gives templates `door.on` and `door.arrival` (`full`, `short` or empty); reading `arrival` on a first visit marks the request, and the middleware `DoorCookie` then sets the session-lifetime cookie `door`. Nothing is stored on the server. A POST answer has no arrival.
- The arrival is CSS at the end of `static/css/app.css`. `static/js/door.js` ends it on the first key or tap and moves the chip: a turn per key, the crescent on Show, a spin while a form is sent, a shake on a refused page. It also sets `data-door-done` on `<html>` inside the app and removes it when a log-out form is sent, so the top bar's mark carries the chip only into and out of the front door.
- An invited Sign up is headed "Join {group}" and names the inviter and the player count (see Entry pages). Log in still says "You're invited to {group}".
- Switch: `DOOR_MOTION=False` removes the movement and the carried names. Check: `web/tests/browser/door.mjs`. [Plan](../plan/1791542366_front_door_revamp.md).

## Arrival after login (2026-10-09)

- `config/door.py` listens to Django's `user_logged_in`, so every way in is covered without a change to a view. The middleware `DoorCookie` sets the cookie `arrived` (30 seconds) on that answer. `door.welcome` is true on the first GET page a signed-in person is shown; `base.html` then writes `data-welcome` on `<main>` and the middleware removes the cookie. A prefetch (`config.prefetch.is_prefetch`) and a signed-out page do not read it; `templates/entry.html` empties the `welcome` block, so Join and Claim pass it on.
- The movement is the `welcome-*` keyframes at the end of `static/css/app.css`. `door.js` ends it on the first key or tap and removes the attribute.
- `static/js/turbo-setup.js` now ignores the browser's "transition was skipped" when a link is tapped while the chip is still being carried in; the screen changes at once.
- Switch: `DOOR_MOTION=False`. Check: `web/tests/browser/welcome.mjs`. [Plan](../plan/1791546778_arrival_after_login.md).
- **On every app open (2026-10-14).** The same arrival plays on the first page of a new window, signed in: the installed app just started, or a new browser tab. `config/door.py` (`door.launch`) sends a signed-in page a short script at the top of the head; it writes `pn-launched` in `sessionStorage` and, when there was none and the navigation is not a reload or Back, `data-launch` on `<html>`. The `welcome-*` CSS answers either mark; `door.js` takes both off when the arrival ends or the page is left. A return from the background plays nothing. Front-door screens (`entry.html`) empty the `launch` block, as they do `welcome`. Switch: `LAUNCH_ARRIVAL=False`, which leaves the arrival after a log-in. [Plan](../plan/1791956781_arrival_on_launch.md).

## Set page (2026-10-09)

- `templates/web/_session_live.html` chooses the page: the felt panel with `details.set-facts` in play, and the `.prep` checklist for a draft or an open set. `web/prep.py` works out each step's state from the summary the page already has; no query is added.
- `_player_row.html` is one row and its sheet sources. `sheets.js` can swap one sheet's content for another's inside the open dialog (`data-sheet-swap`); that is how Cash out is reached on a phone.
- `dock.js` folds the host menu on first sight of a set in play and keeps the host's choice as `open` or `collapsed`. `table.js` holds the movement and remembers the steps in `sessionStorage` to know what changed.
- `GameSession.state_word` gives the words Draft, Open, In play, Counting up, Finalized and Canceled to templates (`state_word` filter) and to refusal messages. No migration.
- The `TABLE_REVAMP` switch and the earlier set page were removed on 2026-10-12, after the human accepted the new one. Check: `web/tests/browser/table.mjs`. [Plan](../plan/1791549025_set_page_revamp.md).

## Count-up in one line and settle-up in rows (2026-10-10)

[Plan](../plan/1791630963_count_up_and_settle_up_revamp.md). The accounting in "End of a set" and "Count-up, review and finalize" still holds; this section describes the screens as built.

**Count-up**

- A player's row is one line: chip, name with what they bought in, and the count field. An empty field is awaiting; a confirmed count shows dim in the field with a tick; a player's own entry shows dim and the row says "entered ₱450". A cashed-out player has no field and shows the amount.
- Tapping a name opens the player's sheet with records, reversals, the exception cash-out and Clear the count. Without JavaScript each row has a Details disclosure.
- The overview has one small mark per player with a buy-in, filled as each is counted or cashed out.
- "The books" lists total bought in, total cashed out, rake when collected, an override when recorded and the set timer, then where the books stand. A discrepancy leads the section and the section moves under the overview once every player is cashed out.
- The help sentence above the list stays in place, so a field never moves when a count is accepted.
- The host bar keeps the running total and the main action when folded. Open, it shows its hint only when there is no action.
- A player sees "Your count" first: the field and Send to host, what they entered, and what the host confirmed.
- `templates/web/_count_v2.html`, `_count_rows.html`, `_count_own.html` and `_books.html`. The field keeps `data-count-input`, `data-saved`, `data-entered` and `data-keep`, so `counts.js` and `numpad.js` are unchanged.
- The `COUNT_REVAMP` switch and the earlier count-up were removed on 2026-10-12, after the human accepted the new one. Checks: `count_flow.mjs`, `end_set.mjs`, `dock.mjs`, `player_entries.mjs`.

**The closed session page**

- Order: overview, Who pays whom, Session results, Sets, Payment records (closed), then View session recap and Manage this session.
- The overview's headline is the viewer's own part: You pay, You receive, You're settled or Nothing to pay. The host's is Still to pay for the table, or Settled. The amount is what is still unpaid.
- A transfer is one row: payer, arrow, payee, amount; beneath it Not paid, or Paid with the time and "marked by the host". The host's Mark paid or Undo is on the row. The viewer's own rows are marked "(you)". The order is the plan's.
- "How this is worked out" holds the notes on netting and rake.
- When Mark paid is accepted the row settles and the bar moves; when the last transfer is paid, "Settled" arrives once per session per browser (`settled:<session>` in localStorage; a player's own key adds their member id).
- `templates/web/night.html`, `_night_lead.html`, `static/js/settle.js`; `settlement.queries.NightOutcome.part_for()` gives the viewer's part from the transfers already loaded.
- The open session page keeps its overview; its Manage section is at the end of the page too.
- Check: `night.mjs`.

## Reopen a set or a session (2026-10-11)

A host can take back a finalized set or a closed session to correct a mistake or to keep playing. Nothing recorded is removed. [Plan](../plan/1791699815_reopen_set_and_session.md).

- **Reopen set.** On a finalized set's page, under “Found a mistake?”. A sheet lists what happens and asks what needs correcting; the reason is required. The set returns to counting up. Reverse a cash-out or a buy-in, count again, cash out, and finalize: the results are revision 2. The earlier revision stays in the set log, struck and marked Replaced, with the reason.
- **A missed buy-in.** While a reopened set is counting up, a player's sheet has “Add a missed buy-in” for the host. It adds the buy-in (and its rake) and leaves the player's cash-out as it is. An ordinary count-up still refuses buy-ins.
- **Reopen session.** In “Manage this session” on a closed session. Refused while any transfer is marked paid: mark those unpaid first. The session is open again: start another set, or reopen a set. The transfer list is retired and kept under “Earlier transfer lists”; closing writes a new one, every transfer unpaid.
- **Order.** A set of a closed session cannot be reopened by itself. Its page says to reopen the session first.
- **While reopened.** A reopened set is left out of the session's results. A reopened session is left out of the stats and of “to settle” on the home page. Both return, corrected, after finalize and close.
- **What everyone sees.** A brass line on the page: “Reopened to correct.” with the reason, who and when; “Corrected.” on the final page of a set finalized again; “Reopened.” on the open session. On a set page the line's rule draws once per reopening and browser.
- Resume play is available on a reopened set only when no later set of the session has started, as before.
- The closing recap does not open by itself a second time; “View session recap” shows the corrected figures.
- Switch: `REOPENING=False` hides both controls and makes both services refuse. Check: `web/tests/browser/reopen.mjs` with `seed_reopen.py`.

## Share results (2026-10-11)

Any member can send a closed session to the group chat as a picture and a short text. Nothing is written and nothing is readable without a login. [Plan](../plan/1791701751_share_results.md).

- **Where.** "Share results" under "View session recap" on a closed session, and at the foot of the recap. Not on an open or archived session.
- **The card.** A picture 1080px wide, as tall as it needs: the table, the date and place, players, sets and total bought in; every player ranked with their signed result; who pays whom; when the session was closed; "Results are after rake." when rake was collected. No Paid marks. A long table name goes onto a second line; long player names are shortened; amounts never are.
- **The text.** The same figures as lines of plain text. It goes with the picture and is what Copy text copies.
- **On a phone that can share a picture:** Share (the phone's own sheet), Save image, Copy text. Some chat apps keep only the picture and drop the text.
- **Elsewhere:** Save image leads, with Copy text; "Share text" appears where the browser can share text only.
- **If the card cannot be drawn** (the font or the canvas is not available), the sheet is the text and Copy text. Without JavaScript the text is in the page under a "Share results" disclosure.
- **After a correction.** A session reopened and closed again shares the new figures and the new "Closed" time. A picture already sent does not change.
- Shares are not logged.
- Switch: `SHARE_RESULTS=False` removes the control. Check: `web/tests/browser/share.mjs` with `seed_share.py`.

## Home screen suggestion and Join with a link (2026-10-11)

After every sign-up or login in a phone's browser, a sheet suggests putting PokerNights on the home screen, with the steps that fit the phone. [Plan](../plan/1791703670_install_prompt.md).

- **When.** On the first ordinary page after a login, about a second in, after the arrival has played. A join or claim page and a session whose recap opens by itself keep the screen; the sheet then shows on the next page. Not on a desktop browser, and never inside the installed app.
- **Android** where the browser offers it: one **Install** button that opens the browser's own install dialog. Accepting ends the suggestion for that browser; declining leaves the menu steps.
- **iPhone:** two steps, Share and then Add to Home Screen, and the line "You log in once more inside the app."
- **A chat app's own browser** (Messenger, Instagram, Viber, Line): says it cannot add apps, to open the page in the real browser, and has **Copy link**, which copies the page it is on. Since 2026-10-16 the front door asks first (below), so this is the back-up for a person who chose Continue here.
- **Any other phone browser:** open the menu, then Install app or Add to Home screen.
- **Closing.** Not now, Close, Escape or a tap outside. It shows again at the next login. **Done, it's on my home screen** ends it for that browser, as does the browser reporting the install.
- **Later.** Your groups ends with **Add to home screen**, which opens the same sheet, until it is marked done.
- **Join with a link.** Inside the installed app, Your groups has a field to paste an invite, claim or reset link copied from a chat, because an iPhone opens tapped links in the browser. A link to another site, or to another kind of page, is refused in words. Paste appears where the phone allows reading the clipboard.
- The page cannot tell that the app is installed when it is opened in the browser, so a person who installed it and logs in from the browser again is asked again unless they said Done there.
- Switch: `INSTALL_PROMPT=False` removes the sheet, the button and the link field. Check: `web/tests/browser/install_prompt.mjs` with `seed_install.py`.

## Invite links shown again (2026-10-16)

Group settings → Invite players lists every active invite with its link, for as long as it works. [Plan](../plan/1792115570_invite_links_shown_again.md).

- **How.** The token is not stored. `Invite.salt` (random, 22 characters) is stored, and the token is `salted_hmac("groups.invite", salt)` under `SECRET_KEY`, base64url (`groups.services.invite_token`). `invite_link_token(invite)` makes it again and returns it only when its hash matches `token_hash`. A database copy alone rebuilds no link.
- **An active row** (not revoked, not expired, not used up): "Created by {name} · {date}", "Used 3 of 20 · expires {date, time}", the address in a read-only field with **Copy** (`copy.js`), **Share** where the phone has a share sheet (text "Join {group} on PokerNights" and the address), and **Revoke** as a quiet action on the left.
- **Cannot be shown:** an invite made before 2026-10-16 (no salt), or one made before `SECRET_KEY` changed. The row says "This link was made before links could be shown again." with Revoke. The link still works.
- **After Create** the page returns with the new link as the top row, marked **New** once (session key `new_invite`, kept through a prefetch). With at least one active link the button is **Create another link** under the list; with none, the primary **Create invite link**.
- **Past invites**, collapsed: the 10 most recent invites that stopped working, without addresses, each "Made {date} by {name} · N joined · revoked {date} / expired {date} / used up". After a revoke its summary takes the accepted-change mark once (`invite_left`).
- Hosts only, as before. Viewing and copying are not audited; creating and revoking are.
- Claim and reset links are unchanged: shown once.
- Switch: `INVITE_LINKS_SHOWN=False` stores no salt, shows no address, and returns the shown-once box after Create. Links made while it was on keep working. Checks: `groups/tests/test_invite_links.py`, `web/tests/test_invite_rows.py`; `web/tests/browser/invites.mjs` with `seed_invites.py`.

## Leave the chat app's browser (2026-10-16)

An invite, claim or reset link tapped in a chat opens in that app's own browser, which cannot put PokerNights on the home screen. The front door now asks the person to open the page in Safari or Chrome before they make an account. [Plan](../plan/1792112551_leave_chat_browser.md).

- **Where.** Join, Sign up, Log in, Claim and Reset, at the top of the sheet. Not on a dead link or on "Sign-up needs an invite". Only in a known chat app's browser on a phone: Messenger, Facebook, Instagram, Viber, LINE and WeChat (`config/chat_browser.py`, from the user agent).
- **iPhone:** "Open this in Safari", the app's name ("Messenger's browser can't keep PokerNights on your home screen."), "Your invite comes with you." when there is one, then two steps: the three dots at the top, then Open in Safari. No page can open Safari from these apps.
- **Android:** "Open this in Chrome" with a primary **Open in Chrome** (an `intent://` link to this exact address, `package=com.android.chrome`), and the same two menu steps under "Or from the menu". If the page is still on screen 1.5 seconds after the tap, a line says to use the three dots and the dots light again.
- **LINE:** **Open in browser**, the same address with `openExternalBrowser=1`, which LINE documents.
- **Copy link** copies the page's full address, token included. **Continue here** folds the card away and remembers it for the browser session (cookie `chat_here`); without JavaScript it is a link to the same page with `here=1`.
- While the card shows, the first field does not take focus, because focus scrolled a short phone past the card. A refused form still focuses the refused field.
- The server decides, so the card is in the first paint and works without JavaScript; front-door answers carry `Vary: User-Agent`. Signed-in pages carry `data-chat-browser` on `<html>` for the home-screen sheet.
- The service worker leaves front-door navigations to the browser ([footgun](footguns/service_worker_user_agent.md)). Offline, those pages show the browser's own error instead of the offline page.
- Not detected: WhatsApp and Telegram, whose link views send the plain browser's user agent. They have their own "Open in browser" control, and the home-screen sheet still follows the login.
- Switch: `CHAT_BROWSER_CARD=False` removes the card. Checks: `web/tests/test_chat_browser.py`; `web/tests/browser/chat_browser.mjs` with `seed_chat_browser.py`.

## The session page updates by itself (2026-10-11)

Everyone with a session page open sees what another person does within about 5 seconds, without a reload. [Plan](../plan/1791706983_session_page_live.md).

- **What arrives:** a transfer marked paid or unpaid (the row settles as it does for the host, and the counts follow), the session closed (the recap then opens by itself once, as on a fresh load) or reopened, a set started, moved on, finalized or reopened, the session archived.
- **What is kept:** the scroll position, open disclosures, and anything typed.
- **It waits** while a sheet is open (recap, share, reopen) or a field has focus or unsaved typing, and lands within a second of that ending.
- **How often:** every 5 seconds; every 20 after two minutes with no change; not at all while the tab or the phone's screen is off, and at once on return. After a failed request it tries again more slowly, up to 30 seconds.
- An archived session is not asked about. Without JavaScript the page is as before.
- A buy-in or cash-out in a set does not redraw the session page; it shows nothing from them until the set is finalized.
- Check: `web/tests/browser/night_live.mjs` with `seed_reopen.py`.

## "Your count" card (2026-10-11)

[Plan](../plan/1791710364_your_count_gap.md).

- On a phone the card sits 16px under the overview panel. Before, it touched that panel and looked tucked under its rounded corners.
- The card shows where the player's count is, in three steps: **Counted** (the player sent it, or the host counted for them), **Confirmed** (by the host), **Cashed out**. A finished step has a tick; the step that is waited for is Brass.
- When the count moves on, on anyone's phone, the player's card is marked for three seconds and the finished step draws in. While the next step is the host's, its mark breathes slowly.
- The card's words, field and button are unchanged. The steps are read out as one sentence ("Step 2 of 3: counted, waiting for the host to confirm.").

## Your groups and a group's sessions update by themselves (2026-10-11)

A person on Your groups or on a group's Sessions tab sees what someone else does within about 5 seconds, without a reload. [Plan](../plan/1791711535_hub_pages_live.md).

- **What arrives:** a session created and its set opened, a set's state (Open, In play, Counting up, Finalized), the number at the table, a new member, the session closed, reopened or archived, a transfer marked paid or unpaid ("you owe", the settle badge).
- **What does not:** buy-ins and cash-outs, which these pages do not show.
- **It waits** while a field has focus or typing, a form such as New group is open, or the page is the answer to a form. It lands within a second of that ending.
- **Group settings and Stats never redraw by themselves.** Group settings shows a new invite, claim or reset link once; a redraw would lose it.
- **How often:** as the session page: every 5 seconds, every 20 after two quiet minutes, not while hidden, at once on return.
- The page asks once as it starts and takes that answer as its starting point. A change made in the instant between the page being drawn and that answer shows at the next change or visit.
- Check: `web/tests/browser/hub_live.mjs` with `seed.py`.

## Seat draw (2026-10-11)

[Plan](../plan/1791717121_seat_draw.md), [study](../study/1791717120_seat_draw.md). Optional. A set starts without it.

- **Where.** An open set with two or more players. "Get this set ready" has an optional step, **Seat draw**, between Open for players and Start the set, with a **Draw** button for a host. Start the set stays the one main button.
- **The draw.** The server shuffles the players at the table (`secrets.SystemRandom`). The first is the dealer; the others sit 1, 2, 3… places clockwise. Each phone plays back that one result, so no two phones can differ.
- **The table (since 2026-10-12, [plan](../plan/1791735776_draw_table_look.md)).** A racetrack with a padded rail, lit felt with a betting line and the app's mark, a chair at every place and a light dealer button; the same on the stage and on the page's still table. During the draw the felt dims and a light travels with the button; the winner gets one brighter moment.
- **The stage.** A full-screen sheet opens by itself on the host's phone at once and on every other phone on the set page at its next update: a drawn table with every player's chip around it, a dealer button that runs around the table, slows, passes the winner by one and springs back (about two and a half seconds since 2026-10-12; about four before), then "{Name} has the dealer seat". A tap skips the part that is playing. Close and Escape leave it; closing counts as having watched.
- **The seat.** The table has one seat per player. The dealer taps any seat on their own phone, or a host taps for them. Everyone else reads "{Name} is choosing a seat". Nobody else's choice is accepted, and a second choice is refused.
- **The seating.** The dealer goes to the tapped seat with the disc; the others are dealt out clockwise in the drawn order, about an eighth of a second apart. Each lands with its first-hand position: dealer, small blind, big blind, under the gun, middle, hijack, cutoff (with two players the dealer is the small blind). The viewer's own chip is ringed and the line says "You are in seat N: {position} on the first hand."
- **On the page afterwards.** A still table with the same seats and the dealer disc, a list clockwise from the dealer with each position, and "Watch the draw". In play the table folds into one line, "Seats · {Name} dealt first", and the list gives seat numbers; positions are for the first hand only.
- **Start without a choice.** If the set starts before a seat is chosen, the dealer takes the top seat.
- **Draw again** (host, before the start) replaces the draw for everyone. The earlier draw is kept, not current; the set log has both.
- **The table changes before the start** (a player joins or is taken off): the draw is marked out of date, the page says "The table changed." and a host can draw again.
- **Late and gone.** A player who joins in play has no seat until a host chooses "Seat {name} after {player}"; no earlier place is rewritten. A player marked as left keeps their seat, shown as away.
- **Each set has its own draw.** Seats are not carried to the next set.
- **When a phone plays it.** Once per draw and browser, and only when it learns of the draw from an update or within two minutes of it; a phone that opens the page later sees the table. While a draw waits for a seat the set page asks the server every 1.5 seconds for those two minutes, so the phones seat within about a second and a half of each other.
- **Without JavaScript** Draw and the seats are ordinary forms and the result is the still table and the list. **Reduced motion** shows each result at once.
- Switch: `SEAT_DRAW=False` hides the step and the table and makes the three services refuse. Check: `web/tests/browser/seat_draw.mjs` with `seed_seat_draw.py`.

## Carried transfers (2026-10-11)

[Plan](../plan/1791728777_carried_debts.md), [study](../study/1791728776_carried_debts.md). Unpaid transfers of earlier sessions can be folded into a later session's settle-up when it is closed.

- **Before closing.** In the Settle up sheet, above "Close session and settle up", a host sees "Carry unpaid transfers from earlier sessions": each transfer that qualifies, with its table and date, ticked. Any can be unticked. A line under the list counts the ticked ones. With none that qualify the close looks as before.
- **What qualifies.** A transfer of the same group and the same unit, in the current list of a closed session that is not archived, not marked paid, not carried already, whose payer and payee both have a result in the session being closed. Any table.
- **Closing.** Each ticked transfer moves its amount from the payer's balance to the payee's, on top of the session's results; the balances still sum to zero and the same netting writes the fewest transfers that clear them. The list can therefore name different pairs than the earlier transfers did. Every ticked transfer is checked again under lock; if one was paid, carried elsewhere or no longer qualifies, nothing is closed and the page says so.
- **The later session's page.** "Who pays whom" is the netted list. Under it, "Includes N unpaid transfers from earlier sessions" opens them, each "{payer} owed {payee}" with a link to its session. A person whose earlier transfer was taken over sees how their figure is made up: this session's balance, each carried debt with its sign, and "To settle".
- **The earlier session's page.** The transfer reads "Carried to {table}, {date}" with a link, has no Mark paid button, and is neither paid nor unpaid. The session is Settled once every transfer is paid or carried; the summary says how many were carried. An open page shows this by itself within a few seconds.
- **Totals.** A carried transfer leaves "you owe", "you are owed" and "still to pay" everywhere; its amount is inside the later session's transfers. What each person owes over all sessions is the same before and after.
- **Undo.** Reopening the later session retires its list, as before, and every transfer it had carried is unpaid again; no row is changed. Closing it again asks again.
- **Refused.** Marking a carried transfer paid ("Mark it paid there."). Reopening an earlier session while one of its transfers is carried ("Reopen that session first.").
- **Chains.** The later session's own unpaid transfers can be carried into the next one.
- **Unchanged.** Results, stats and the recap's ranking describe play. The recap and the share text say that the transfers include earlier unpaid ones.
- Switch: `CARRY_DEBTS=False` offers no list and carries nothing; transfers already carried stay carried. Check: `web/tests/browser/carried_debts.mjs` with `seed_carried.py`.

## Table alerts (2026-10-15)

[Plan](../plan/1792069342_table_alerts.md), [study](../study/1792069341_table_alerts.md). A player put in a set by someone else hears about it, on their phone and in the app, and a player watching the set sees who was just added.

- **Who is told.** When a host opens a set, each player already added who has a login, other than the host who tapped. After that, each player a host adds while the set is open or in play, at that moment. A player who joins by themselves is not told; a no-login roster player cannot be. Each player is told once per set (`notify.Notice`, unique per player and set), so closing and opening again tells nobody twice.
- **The words.** "Friday table · set 2 is open", "Ana added you. Tap to see the table." when the set opens; "Friday table · you're in set 2" for a later add, with "Play has started." while in play. No amounts and no other names.
- **On the phone.** A phone with table alerts on gets a notification; a tap opens the set in the app's window. An iPhone takes alerts only in the app on the Home Screen (iOS 16.4 or later). The send runs after the commit, in the host's request, one request per phone in parallel, 5 seconds at most each; a failure is logged and never refuses the host's action. A phone the push service has forgotten (404, 410) is removed.
- **Turning alerts on** (since 2026-10-16, [plan](../plan/1792163903_alerts_bell.md)). A bell in the header of every signed-in page, before the name, where this phone can take alerts. Its shape says the state: outline (off), filled (on), slashed (blocked); its name says it too ("Table alerts, on"). A tap opens a small panel under it: "Get a notification when a host adds you to a set." and **Turn on**; or "On for this phone." with **Turn off**; or "Alerts are blocked for PokerNights in this phone's settings." Escape, a tap outside or the bell closes it; going to another screen closes it; a refresh of Your groups leaves it open. The browser's question comes from the tap on Turn on, never on its own. In an iPhone's browser the bell shows too, and its panel says "On an iPhone, alerts work from the Home Screen app." with **Add to Home Screen**, which opens the home-screen sheet. Where neither works, no bell. A phone with alerts on tells the server its subscription once per window, so a phone that another person logs in on follows that login.
- **The reminder** (2026-10-16). Once per window (an app launch), on Your groups with a group, for a phone whose permission is unasked: the bell's panel opens by itself with **Not now**, and the bell swings once. It waits for the arrival (about 1.4 seconds after a login, 0.8 otherwise) and gives way to any open sheet, the home-screen sheet first; it then comes at the next start of Your groups in that window. Never on another page, never when on or blocked. `sessionStorage` `pn-alerts-reminded`; without storage there is no reminder. The 30-day Not now of the old foot panel is gone and its key removed.
- **In the app.** A card on Your groups whose set added the viewer says "Ana added you" with a brass dot, and its button leads, until the viewer opens the set. A refresh of Your groups brings it in.
- **On the set page, for everyone else.** A player added by someone else gets the brass mark and "Joined" ("You're in" on the viewer's own row) for three seconds, with or without motion; the players count draws its brass line. When the new row is out of view, a toast names who joined ("Ana and Ben joined") with **Show**, which scrolls to the row and marks it again; when it is in view, screen readers hear "Ana joined the set.". The host's own add is marked but not announced. Nothing is announced in a hidden tab.
- **The next set** (2026-10-15, [plan](../plan/1792073300_next_set_for_players.md)). **Play set N** tells each player carried into the new set, other than the host: "Friday table · set 2 is open", "ari started set 2. You're at the table.", and "ari started set 2" on Your groups (notice kind `next`). Every phone on the previous set's page (counting up, final or canceled) shows within a poll "Set 2 has started", a line saying whether the viewer is at its table, and **Go to set 2**; the final page's own button leads there too. The page learns of it without a write to the previous set: an ended set's live version is "{version}.{later set}" (`web.views.later_set`, `live_version`), asked only for an ended set. A count form on the previous set stays as it was. Switch: `NEXT_SET_NOTICE=False` returns those pages to before; the alert follows `PUSH_ALERTS` and `TABLE_NOTICES`.
- **Endpoints.** `POST /alerts/subscribe/` (the browser's `PushSubscription` as JSON; an upsert by its unique endpoint) and `POST /alerts/unsubscribe/`, login and CSRF as everywhere.
- **Switches.** `PUSH_ALERTS=False` (or a missing VAPID key) sends nothing and hides the bell and the reminder. `TABLE_NOTICES=False` hides "added you". `ARRIVAL_MARKS=False` returns the set page to the 12px rise alone. `SERVICE_WORKER=False` removes the worker and the alerts with it.
- **Checks.** `notify/tests/` and `web/tests/test_table_alerts.py`; in a browser, `web/tests/browser/arrivals.mjs` and `alerts_bell.mjs`, each on its own fresh `seed_arrivals.py` (the phone's push service stubbed). Real delivery is checked on a phone.

## Profile (2026-10-17)

[Plan](../plan/1792238274_profile_page.md).

- **The way in.** Tap your chip at the top right, then **Your profile**. The address is `/me/`. **Name and password** under your name goes straight to the settings.
- **Your record across groups.** All time or This year. Pesos from all your groups add up to one figure, with a running-profit chart and four tiles (win rate, average, best night, worst night; the best and worst name their group). **By group** lists each group with its share; a group at zero reads "Even". **Chips games** lists each chips group with its own figure; chips are never added up across groups.
- **Which groups count.** Every group you joined, except archived groups. A group you were removed from still counts, but its row is not a link, because its pages are for members.
- **Your name.** One field renames you in every group you are in. A group where someone else has the name is skipped, and the message names it. Your login username does not change. When your names differ between groups, the row says "Differs by group" and lists them.
- **Password.** Give the current password and a new one (the sign-up rules). This phone stays logged in; other phones and browsers are logged out; live reset links stop working. After five wrong current passwords in 15 minutes the form refuses and says how long to wait. The same change sent twice succeeds once and counts no wrong try.
- **Checks:** `web/tests/test_profile.py`, `accounts/tests/test_change_password.py`; browser `web/tests/browser/profile.mjs` with `seed_profile.py`.

## Sessions tab

The group's Sessions tab leads with the viewer's own table, then lists their past nights. [Plan](../plan/1792243014_sessions_tab_redesign.md).

- **Now playing.** One card for each session in progress. A card shows the table, the location and the date ("Today" for today in Manila), the latest set and its state, up to six seated players' chips with "+N", "N at the table", and the clock while the set is in play. A set in play is felt; every other state is a neutral panel.
- **Order.** Sets in play where the viewer sits, other sets in play, the viewer's open or ended sets, other open or ended sets, then drafts (hosts only). Inside each band: the earliest date, then the oldest session.
- **Your table.** A card where the viewer sits says "You're playing" (or "You're at this table" before play). The first such card has the one bone action: **Open the table**, **Open set N** or **Go to the session**. Another card of the viewer's has the same label in the secondary style.
- **Where a card leads.** The latest set while it is unfinished, else the session. The group card on Your groups uses the same rule (`web.sessions_tab.destination`).
- **New session** (hosts with a table) comes after the cards, as a secondary button.
- **Past sessions.** Grouped by month, newest first. This year's months are open; each earlier year is one closed disclosure ("2025 · 48 sessions"). With nothing this year, the newest year is open. Each row: the table, "date · N sets · status", the viewer's net in the session's unit ("Even" for zero, "Did not play" if absent), and one line for each transfer the viewer still pays or receives ("You pay Carlo ₱500", "Dina pays you ₱200").
- From 700 px of content width the cards are in two columns. A single card takes the full width.

