# A page the service worker fetched carries the worker's user agent

## Trigger

The server reads the `User-Agent` header to tell a chat app's browser (`config/chat_browser.py`), and the service worker answers navigations with `fetch(event.request)` so that it can show the offline page.

## Observed behaviour and impact

On 2026-10-16 `install_prompt.mjs` set Messenger's user agent on the page and logged in. The login page arrived with `data-chat-browser="ios"`; Your groups, fetched through the worker, arrived without it. A request the worker makes is sent with the worker's user agent, and the browser check overrides only the page's. Android's WebView is reported to behave the same way: an app's user-agent string is set on the WebView, not on its service workers. A person in Messenger who had visited before would have seen no card asking them to leave.

## Remedy

The worker does not answer navigations to `/accounts/`, `/join/` or `/claim/` (`FRONT_DOOR` in `config/pwa.py`), so the browser asks for them itself with the page's user agent. The home-screen sheet (`install.js`) reads `navigator.userAgent` in the page as well as the server's mark, because signed-in pages still go through the worker.

## Limits of the evidence

Headless Chrome shows the difference because its user-agent override does not reach the worker. Whether a given chat app's WebView does the same was not tested on a phone. The remedy holds either way.
