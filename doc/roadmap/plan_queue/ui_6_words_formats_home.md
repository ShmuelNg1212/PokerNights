# Words, formats and the home card (queued)

Status: queued 2026-11-19 from the [whole-app UI critique](../../study/1795101392_ui_critique.md). Reconstitute against the current code before approval. Mode: design. Critique issues 7 and 8 (P3) and the minor observations. Skill: `/impeccable clarify`.

## Draft tasks

- [ ] "Usual" everywhere: the buy-in quick amount says "Default" (`templates/web/_buy_in_form.html:11`).
- [ ] 12-hour times everywhere ("11:07 PM"). The session page shows "23:07".
- [ ] Set settings: a locked set gets its own intro. Now it says "Configure rake before the first buy-in" (`templates/games/settings_form.html:9`).
- [ ] New session: show the date as "Thu, Nov 19" next to the native field.
- [ ] Amount fields group digits ("1,000") or show the ₱ prefix; blinds and buy-in fields in Set settings show the unit.
- [ ] Home card: the gear shows to hosts only (`templates/web/_group_card.html:6`).
- [ ] Home card tokens: the people who played recently, not the first six alphabetically.
- [ ] "And 3 more unpaid transfers in past sessions." links to the Not settled filter.
- [ ] A player who left: show the net large, the cash-out small.
- [ ] Stats: a cue that the sort chips scroll; a kinder empty line for a host who has not played.
- [ ] Small text: review the 12 px secondary text on the group page (76 pieces under 14 px). Raise what a player reads at the table to 13 px or more. Use the type ramp only.
- [ ] `templates/offline.html:14`: use a ramp size.
