# The account panel keeps its first-drawn state

`templates/_account.html` is `data-turbo-permanent`. Turbo moves the same element from page to page and never draws it again. Anything in it that depends on the current page (an `aria-current`, a highlight, a count) is right only on the first page that drew it and stays stale after that.

Do not put page-dependent state in the panel. If it is necessary, set it in JavaScript on `turbo:load`.
