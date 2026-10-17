# The hub stamp counts seats, not who sits

- **Trigger:** between two polls of Your groups or the Sessions tab, one player leaves an unfinished set and another joins it.
- **Observed:** `settlement.queries.hub_stamp` records how many players sit at each unfinished set, not which ones. The count does not change, so the page does not redraw.
- **Impact:** the chips on a Sessions tab card can show the earlier player until the next change that the stamp sees.
- **Remedy:** accepted for now; the next change redraws the card. If a page must show who sits, add the seated member ids to the stamp.
