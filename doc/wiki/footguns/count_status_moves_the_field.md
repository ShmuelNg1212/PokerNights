# A saved-count status can move its field

Date: 2026-10-05, Asia/Manila.

**Trigger.** Confirm a typed count in place on a phone. The new Ready to cash out badge and saved amount wrap onto an extra line above the field.

**Observed behavior.** The document keeps its scroll position, but the field moves down. After the count-up redesign, `inplace.mjs` measured 324px before confirmation and 358px after it. The former per-row Confirm selector also had to change to the shared `data-confirm-typed` button.

**Impact.** The count the host was looking at shifts beneath their finger even though there is no page reload. Keeping `scrollY` alone is not enough when content inside the row grows.

**Remedy.** `static/js/counts.js` remembers a visible typed field's ID, top and scroll position on `turbo:submit-start`. After the matching in-place update and Turbo's scroll restoration, it adjusts once to keep that field's position. It leaves a changed scroll position alone. It accounts for a row's current motion transform, resets on failure and page stop, and does not animate money or scrolling.

**Evidence.** The corrected `inplace.mjs` passes all 38 checks on fresh synthetic fixtures. The field top is 324px both before and after confirmation; a reason in another form and its open Details are preserved. See the [plan](../../plan/1791202390_host_gaps_numpad_count_up.md).
