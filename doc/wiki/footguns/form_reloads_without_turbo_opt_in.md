# A form without data-turbo="true" reloads the page

- **Trigger:** A POST form on a page with in-place updates, without `data-turbo="true"`.
- **Observed behavior:** Turbo runs with `Turbo.config.forms.mode = "optin"` (`static/js/turbo-setup.js`). The form posts natively. The browser loads the whole page again at the redirect target, for example `/n/1/#coming`. The page jumps, open disclosures fold, and no `turbo:render` or `inplace:updated` event fires. Motion that listens for those events does not run.
- **Impact:** Found on 2026-10-27 in the host's RSVP rows. Marking a player in reloaded the page and folded Not answered. Nothing stored was affected.
- **Remedy:** Add `data-turbo="true"` to a form that should update its page in place. The view must redirect back to the same path (`config/inplace.py`). Check in the browser that a value set on `window` survives the answer (`rsvp.mjs`, "the answer updates in place").
- **Not changed:** Forms that leave the page, or that must load afresh, stay native.
