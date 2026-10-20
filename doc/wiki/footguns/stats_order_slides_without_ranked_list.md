# A new order slides the whole board when nobody is ranked

- **Trigger:** on the Stats tab, a viewer taps an order pill (Profit, Average, …) while no player is ranked. Example: a short period, or Per hour when little time was recorded.
- **Observed:** the figures slide in from the side as one block. When some players are ranked, each row moves to its new place instead. This does not depend on the role: a host and a player on the same board see the same movement.
- **Cause:** `arrived()` in `static/js/stats.js` moves rows one by one only inside `[data-stat-board]`. `_group_stats.html` draws that list only when a player is ranked. Without the list, the code uses the slide for a new period or unit. The "Not ranked yet" list has no `data-stat-board`, so on a mixed board its rows change place without movement.
- **Impact:** appearance only. The figures and the order are correct.
- **Remedy:** accepted (2026-10-20). To change it, let `places()` and `arrived()` also read the "Not ranked yet" rows.
