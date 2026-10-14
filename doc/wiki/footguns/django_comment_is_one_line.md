# A Django `{# #}` comment is one line

Date: 2026-10-14, Asia/Manila.

**Trigger.** A `{# ... #}` comment in a template that runs over more than one line.

**Observed behavior.** Django prints it as text. In `base.html` it landed in the `<head>`: the browser ends the head at the first text and puts everything after it in the body. With the comment above the stylesheet, `welcome.mjs` lost the chip carried in from the log-in page and reported "Transition was aborted because of invalid state. ViewTransition opt-in disabled" on every server, even those that sent nothing else new.

**Impact.** The stylesheet's `@view-transition` opt-in stops counting, so screen changes lose their movement, and the stray words can show on the page. Nothing in the Django suite noticed until a test looked at the head's text.

**Remedy.** Use `{% comment %}...{% endcomment %}` for a comment over several lines. `accounts/tests/test_door.py` (`LaunchArrivalTests`) checks that a signed-in page's head holds nothing but tags.
