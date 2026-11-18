# The felt stays in view only outside its column

**What happens.** `position: sticky` on the felt does nothing on a phone. The felt scrolls away with the page.

**Why.** A sticky box stays in view only inside its parent. In play the felt's parent is `aside.table-left`, which holds only the felt, the seat table and the host menu. The players list is outside it, so the aside ends just below the felt.

**Do this.** On a phone, give `.table-left` `display: contents` while it holds the felt. The felt's parent is then `.table-layout`, which holds the list too. See "In play the felt stays under the header" in `static/css/app.css`. Keep these points:

- The sticky rule must win over `html[data-felt-lit] #live .felt`, which sets `position: relative` while the felt is lit after the overture. Its selector has more classes.
- `top` is the header's height, 69px. With the offline notice the header moves down by `--offline-h`, and the felt moves with it.
- A focused row needs a larger `scroll-margin-top` (340px), or it comes to rest under the felt.
- A screen under 600px tall keeps the felt in the page. There it would leave about two rows above the dock.

**How it was found.** Browser checks at 390 × 844 and 320 × 568 in Chromium and WebKit (2026-11-19).
