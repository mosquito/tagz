# tagz + htmx + aiohttp demo

A tiny aiohttp app that builds every byte of HTML with **tagz** and uses
**htmx** to live-swap three server-rendered fragments:

- **Server time** — refreshes every second
- **Your IP** — loaded on page load with a refresh button
- **`tagz` on PyPI** — fetched from the PyPI JSON API and rendered

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
  tagz to `hx-get="/now"` — no string-mashing needed.
- **HTML fragments from aiohttp handlers.** Each endpoint returns a
  partial HTML string built by tagz, not JSON.
- **Pre-resolving async data.** The PyPI handler `await`s the response
  first, then passes plain Python values into the tag tree. See
  [Async and tagz](https://mosquito.github.io/tagz/explanation/async-and-tagz.html)
  for the design rationale.
- **Inline CSS.** A `StyleSheet({selector: Style(...)})` block in
  `<head>` — no separate CSS file.
- **`Fragment` for wrapper-less responses.** The `/now`, `/ip`, and
  `/pypi` endpoints return raw HTML pieces that htmx splices into the
  page, with no extra container.

## Files

- `server.py` — the whole demo, ~190 lines.
- `requirements.txt` — runtime deps for non-uv users.
