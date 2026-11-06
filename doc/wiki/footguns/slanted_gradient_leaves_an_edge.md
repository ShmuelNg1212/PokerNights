# A slanted gradient on a narrow box leaves a hard edge

**What happens.** A `linear-gradient(105deg, transparent 10%, light 50%, transparent 90%)` on a tall band, such as one that is 70% of the felt's width and its full height, shows a hard vertical edge. The edge is on the box's right side near the top, and on its left side near the bottom.

**Why.** An angled gradient line runs from corner to corner. The box's top-right corner is not at 100% of that line. In the felt band it was at about 80%, where the light is still about a quarter strong. The box ends there, so the light ends in a straight line.

**Do this.** Use a horizontal gradient (`90deg`), which is clear at both side edges at every height. Get the slant from `skewX()` in the same `transform` that moves the band. See the felt light in `static/css/app.css` (`felt-light`).

**How it was found.** Frames of the felt light paused at 300 ms at 1280 px and at 420 ms at 390 px (2026-11-06).
