# Rake controls

Date: 2026-10-04. Status: complete. Repository baseline: main `7011a71`, clean working tree.

## Outcome

Make it clear how a host enables rake and chooses a flat amount or percentage of each gross buy-in. Make the choice available before default opening buy-ins lock the rule.

Sources: AGENTS.md, PRODUCT.md, DESIGN.md, current wiki and [approved rake plan](../plan/1791093380_set_rake_and_group_pool.md). The prior approved rules deduct rake from gross buy-ins, track already-collected group totals, and lock the rule while accepted money exists. This request does not explicitly change those accounting rules.

## Evidence and diagnosis

- `SessionForm` has no rake fields. `create_session` creates the first settings version with rake Off. A host must find Change settings before starting to enable rake.
- Starting a set records one default opening buy-in per player unless the host clears that option. `has_money` then disables all rake controls in `SettingsForm`. This is the agreed accounting guard, but the creation flow makes it easy to lock Off unintentionally.
- `SettingsForm.rake_percentage` is a DecimalField with a minimum of 0.01. Its field validation runs even when Flat or Off is selected. Posting a valid flat amount with an unused percentage of `0` fails validation. Mode-specific normalization runs too late to remove that error. Native number constraints can also block submission of an unused field.
- The service already supports Off, Flat and Percentage, validates integer native amounts, and records the selected fee on each buy-in. No missing rake calculation or pool feature was found.

Three hypotheses were tested through real Django forms, views and services on a disposable test database. Command: `.venv/bin/python /private/tmp/pn-rake-controls-probe.py`. In 0.281 seconds, the opening-buy-in lock probe passed; the creation-choice and inactive-percentage regression probes failed as expected. Temporary evidence: `/private/tmp/pn-rake-controls-probe.log`. No development game records or implementation files were changed.

Baseline: `DEBUG=True .venv/bin/python manage.py test` ran 465 tests in 15.989 seconds, passed with ten PostgreSQL-only skips. This existing suite does not catch the two control defects.

## Options and recommendation

1. Only change labels in Change settings. Small, but it leaves the missing early choice and inactive-field validation defect.
2. Add a shared native rake section to New session and Change settings. Offer Off, Flat amount, and Percentage of buy-in explicitly. Validate only the selected value; normalize unused parameters to zero. Explain and link the pre-start choice on subsequent sets. Recommended: this fixes the observed paths without changing recorded money.
3. Allow rake changes after buy-ins. This needs new rules for prior and later records and changes the approved lock. It is outside this request's confirmed scope.

Use native controls and existing Rack form components. Text inputs with decimal input hints and server validation can avoid inactive browser number constraints without adding another JavaScript module. Both value inputs may remain visible with clear labels and help; only the chosen value applies. A shared form parser must preserve percent precision, integer money and existing stake parsing.

## Risks, external inputs and open questions

The user's exact trigger is unconfirmed. An optional question asks whether the set already had buy-ins. The code proves both failure paths regardless of that answer. Assume the existing accounting lock remains required; no retroactive fee, reversal or data rewrite is proposed.

Session creation must validate the rake before writes and store it in the initial settings version. Invalid active values must leave no partial session. Disabled locked controls must retain the saved rule during ordinary stake edits. Unit changes must retain the existing Off reset. Presets remain stakes-only; next sets keep their current inheritance rule.

No external service, new dependency or schema change is expected. Browser verification must cover native submission, keyboard use, pesos and chips, initial and later sets, stale inactive inputs, and locked settings. The existing cumulative added-JavaScript budget has only 526 bytes remaining, so prefer no additional JavaScript.
