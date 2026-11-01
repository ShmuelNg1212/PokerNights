# Mobile emulation widens innerWidth

A browser script that emulates a phone with `mobile: true` cannot find sideways scroll by comparing `scrollWidth` with `innerWidth`. The layout viewport grows to fit the content, so the two figures match and the check always passes.

Compare `document.documentElement.scrollWidth` with the width the script asked for. `surfaces.mjs` does this. Older scripts that use `innerWidth` give a weaker check than their names say.
