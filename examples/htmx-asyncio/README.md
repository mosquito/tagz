# tagz + htmx + aiohttp demo

A small aiohttp app that builds every byte of HTML with **tagz** and
uses **htmx** to live-swap server-rendered fragments:

- **Server time** — refreshes every second
- **Your IP** — loaded on page load with a refresh button
- **`tagz` on PyPI** — fetched from the PyPI JSON API
- **Greet form** — text input → POST → escaped response fragment
- **Counter** — server-side state, `+/−` buttons re-render the value

No JSON between client and server. No templating engine. Just Python →
HTML → DOM.

## Run

With [uv](https://docs.astral.sh/uv/) (recommended):

```bash
uv run --with aiohttp python examples/htmx-asyncio/server.py
```

Or with plain pip:

```bash
cd examples/htmx-asyncio
pip install -r requirements.txt
python server.py
```

Open <http://127.0.0.1:8080/>.

## What this example shows

- **HTMX attributes as Python kwargs.** `hx_get="/now"` is rewritten by
  tagz to `hx-get="/now"` — no string concatenation.
- **HTML fragments from aiohttp handlers.** Each endpoint returns a
  partial HTML string, not JSON.
- **Pre-resolving async data.** The PyPI handler `await`s the response
  first, then passes plain Python values into the tag tree. See
  [Async and tagz](https://mosquito.github.io/tagz/explanation/async-and-tagz.html).
- **Components are just functions.** `card(title, *body)`,
  `render_counter_widget()`, `render_greet_form()` — each is a
  reusable Python function that returns a tag tree. Composition
  is regular `def`.
- **Server-side state.** The counter lives in a module-level `dict`.
  Clicks POST → the handler mutates the dict → returns the new
  `<span>` for htmx to swap in. The client never holds state.
- **Form handling.** The greet form posts `name=...` to `/greet`; the
  handler reads `await request.post()`, builds a `<p>` or a `<span>`,
  returns it. User input is HTML-escaped by tagz automatically —
  the included XSS test (`<script>alert(1)</script>` as a name)
  renders as `&lt;script&gt;…&lt;/script&gt;`.
- **Inline CSS.** A `StyleSheet({selector: Style(...)})` block in
  `<head>`, no separate CSS file.
- **`Fragment` for wrapper-less responses.** Endpoints return raw
  HTML pieces; htmx splices them in without an extra container.
- **SSR security.** All responses go through `html_response(...)`
  which sets `Content-Type: text/html; charset=utf-8`,
  `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`,
  and a `Content-Security-Policy` that allows only the htmx CDN
  for scripts and forbids framing. The same CSP is also emitted as
  a `<meta http-equiv>` in case the page is served somewhere that
  strips headers.

## Files

- `server.py` — the whole demo, ~300 lines.
- `requirements.txt` — runtime deps for non-uv users.
