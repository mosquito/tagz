# Serve HTML fragments to htmx

**Problem.** You want to build a small server-rendered app where the
browser uses [htmx](https://htmx.org/) to swap in fragments of HTML
without writing any JavaScript.

**Solution.** Render the page and the fragments with `tagz`, return
them as plain `text/html` from your handler. htmx attributes are
just hyphenated kwargs — `hx_get="/click"` becomes `hx-get="/click"`.

## The page

<!-- name: test_htmx_index_renders -->
```python
from tagz import Page, html

def index_html() -> str:
    return Page(
        lang="en",
        head_elements=(
            html.meta(charset="utf-8"),
            html.title("htmx + tagz"),
            html.script(src="https://unpkg.com/htmx.org@2.0.3"),
        ),
        body_element=html.body(
            html.button(
                "Click me",
                hx_get="/click",
                hx_swap="outerHTML",
            ),
        ),
    ).to_html5()


out = index_html()
assert 'hx-get="/click"' in out
assert 'hx-swap="outerHTML"' in out
```

## The fragment

When htmx fires `GET /click`, the server returns a chunk of HTML
that replaces the button.

<!-- name: test_htmx_fragment -->
```python
from tagz import html

def click_html() -> str:
    return str(html.span("clicked!"))

assert click_html() == "<span>clicked!</span>"
```

## Wire it into aiohttp

<!-- name: test_htmx_aiohttp_app -->
```python
from aiohttp import web
from tagz import Page, html


async def index(request: web.Request) -> web.Response:
    page = Page(
        lang="en",
        head_elements=(
            html.meta(charset="utf-8"),
            html.title("htmx + tagz"),
            html.script(src="https://unpkg.com/htmx.org@2.0.3"),
        ),
        body_element=html.body(
            html.button("Click me", hx_get="/click", hx_swap="outerHTML"),
        ),
    )
    return web.Response(text=page.to_html5(), content_type="text/html")


async def click(request: web.Request) -> web.Response:
    return web.Response(text=str(html.span("clicked!")), content_type="text/html")


app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/click", click)
# In a real script: web.run_app(app, host="127.0.0.1", port=8080)

assert app.router.named_resources() == {}  # routes are unnamed by default
assert len(app.router.resources()) == 2
```

That's the whole app. Open the page, click the button, the button
disappears and the `<span>` takes its place.

## Handling form input

htmx posts the form fields exactly the way the browser would. On
the server you read them with whatever your framework provides —
`await request.post()` in aiohttp.

### The form

Use a `Fragment` to emit the form and its result container side by
side without a wrapping `<div>`.

<!-- name: test_htmx_form_renders -->
```python
from tagz import Fragment, html

def greet_form_html() -> str:
    return str(Fragment(
        html.form(
            html.label(
                "Your name ",
                html.input(type="text", name="name", required=True),
            ),
            html.button("Greet", type="submit"),
            hx_post="/greet",
            hx_target="#greeting",
            hx_swap="innerHTML",
        ),
        html.div(id="greeting"),
    ))


out = greet_form_html()
assert 'hx-post="/greet"' in out
assert 'hx-target="#greeting"' in out
assert 'name="name"' in out
assert "required" in out
```

### The response fragment

After `POST /greet`, the server returns the HTML that replaces the
`<div id="greeting">` body. Build it from plain strings; tagz
escapes user input automatically.

<!-- name: test_htmx_form_response -->
```python
from tagz import html


def greet_response_html(name: str) -> str:
    name = name.strip()
    if not name:
        return str(html.span("Please enter a name."))
    return str(html.p(f"Hello, {name}!"))


assert greet_response_html("Ada") == "<p>Hello, Ada!</p>"
assert greet_response_html("") == "<span>Please enter a name.</span>"
# User-controlled text is escaped — no XSS even on direct interpolation.
assert greet_response_html("<script>alert(1)</script>") == (
    "<p>Hello, &lt;script&gt;alert(1)&lt;/script&gt;!</p>"
)
```

### The aiohttp handler

<!-- name: test_htmx_greet_handler -->
```python
from aiohttp import web
from tagz import html


async def greet(request: web.Request) -> web.Response:
    form = await request.post()
    name = (form.get("name") or "").strip()
    if not name:
        body = html.span("Please enter a name.")
    else:
        body = html.p(f"Hello, {name}!")
    return web.Response(text=str(body), content_type="text/html")


app = web.Application()
app.router.add_post("/greet", greet)
assert any(r.method == "POST" for r in app.router.routes())
```

`form.get("name")` is a `str` (or `None`). tagz escapes it on the
way out — interpolating user input into a child or attribute is
always safe by default. See
[The escaping model](../explanation/escaping-model.md) for the
details.

## Components: just functions returning tags

A "component" in `tagz` is any function that returns a `Tag` or a
`Fragment`. There is no special class or decorator — composition is
ordinary Python function composition.

<!-- name: test_htmx_components -->
```python
from tagz import Fragment, html


def card(title: str, *body) -> "Fragment":
    return Fragment(
        html.div(
            html.h3(title),
            *body,
            classes=["card"],
        ),
    )


def stats(items: list[tuple[str, int]]):
    return html.ul(*(html.li(f"{label}: {value}") for label, value in items))


page_body = card(
    "Server stats",
    stats([("uptime (s)", 42), ("requests", 1337)]),
)

rendered = str(page_body)
assert '<h3>Server stats</h3>' in rendered
assert "<li>uptime (s): 42</li>" in rendered
```

Same component, different data, different output — that's the
entire component model. No props validation, no class hierarchy.

## Server-side state with re-render

htmx-driven apps usually keep state on the server (database, in-memory
dict, session). The client never holds it; it just asks the server to
re-render the affected fragment. That's the same loop you'd use for
any SSR app, only the swap is HTML instead of a full page refresh.

### Stateful counter

The whole interaction loop in twenty lines: state lives in a dict,
the `+` and `-` buttons POST to handlers that mutate the dict and
return the **same** fragment (updated value), which htmx swaps into
the page.

<!-- name: test_htmx_counter -->
```python
from tagz import Fragment, html

STATE = {"counter": 0}


def render_counter() -> str:
    return str(Fragment(
        html.span(str(STATE["counter"]), id="counter-value"),
        html.button(
            "−",
            hx_post="/counter/dec",
            hx_target="#counter-value",
            hx_swap="outerHTML",
        ),
        html.button(
            "+",
            hx_post="/counter/inc",
            hx_target="#counter-value",
            hx_swap="outerHTML",
        ),
    ))


def render_counter_value() -> str:
    # The fragment that replaces #counter-value after each click.
    return str(html.span(str(STATE["counter"]), id="counter-value"))


# Initial render
STATE["counter"] = 0
assert 'id="counter-value"' in render_counter()
assert ">0</span>" in render_counter_value()

# Simulate a click on "+"
STATE["counter"] += 1
assert render_counter_value() == '<span id="counter-value">1</span>'

# And the matching aiohttp handler:
from aiohttp import web

async def counter_inc(request: web.Request) -> web.Response:
    STATE["counter"] += 1
    return web.Response(text=render_counter_value(), content_type="text/html")
```

Notice: the **state lives only on the server**. The client gets
just the updated `<span>`. There's no JSON, no client-side state
sync, no hydration. To stop the value getting clobbered if two
clients click at once you'd lift `STATE` into a database — the
rendering code doesn't change.

## Securing SSR fragments

tagz returns HTML, and every byte sits inside an HTTP response that
the browser parses. A few precautions stop that surface from
becoming a foothold.

### What tagz already protects you from

- **String children and attribute values are HTML-escaped by default.**
  Interpolating user input into `html.p(name)` or `html.a(href=user_url)`
  can't smuggle in markup or break out of an attribute. See
  [The escaping model](../explanation/escaping-model.md).
- **`<script>` and `<style>` are intentionally unescaped.** Never
  interpolate user input into them — JSON-encode data and assign it
  to a JS variable instead.
- **`Raw(...)` is opt-in unsafe.** Treat each use site like
  `dangerouslySetInnerHTML`: it must be either pre-sanitised or
  authored content you control.

### Set the response content type explicitly

Always pass `content_type="text/html"` (or `"text/html; charset=utf-8"`).
Without it some clients sniff the body and may guess wrong. Pair it
with the standard "no sniff" header:

<!-- name: test_htmx_response_headers -->
```python
from aiohttp import web
from tagz import html


def htmx_response(body: str) -> web.Response:
    return web.Response(
        text=body,
        content_type="text/html",
        charset="utf-8",
        headers={"X-Content-Type-Options": "nosniff"},
    )


resp = htmx_response(str(html.span("hi")))
assert resp.content_type == "text/html"
assert resp.headers["X-Content-Type-Options"] == "nosniff"
```

### Send a Content-Security-Policy

Even with escaped output, a tight CSP shrinks blast radius if a
fragment ever escapes (e.g. an HTML sanitiser bug, a slipped
`Raw(...)`). For an htmx app you typically need `script-src` covering
the htmx CDN and `style-src` covering your inline styles via a nonce.

<!-- name: test_htmx_csp -->
```python
from tagz import html

CSP = (
    "default-src 'self'; "
    "script-src 'self' https://unpkg.com; "
    "style-src 'self' 'unsafe-inline'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none'"
)


def secure_page_head():
    return (
        html.meta(charset="utf-8"),
        # Allow setting CSP via <meta> when you can't set headers,
        # otherwise prefer the HTTP header form.
        html.meta(http_equiv="Content-Security-Policy", content=CSP),
        html.title("secure"),
        html.script(src="https://unpkg.com/htmx.org@2.0.3"),
    )


rendered = "".join(str(t) for t in secure_page_head())
# Single quotes are HTML-escaped inside attribute values — that's fine,
# CSP parsers see the original character after the browser decodes it.
assert "Content-Security-Policy" in rendered
assert "default-src" in rendered
assert "frame-ancestors" in rendered
```

Drop `'unsafe-inline'` for styles in production by switching to
nonces or external stylesheets. For inline `<script>` blocks (which
you mostly don't need with htmx) use `nonce='...'` and add the same
nonce to the CSP.

### Pin htmx with Subresource Integrity

Loading htmx from a CDN means trusting that CDN to never serve a
different file. Add `integrity` + `crossorigin` so the browser
verifies the script hash and refuses to run anything else.

<!-- name: test_htmx_sri -->
```python
from tagz import html

HTMX_URL = "https://unpkg.com/htmx.org@2.0.3/dist/htmx.min.js"
# Pin the exact sha384 of htmx.min.js. Recompute on version bump:
#   curl -sL "$HTMX_URL" | openssl dgst -sha384 -binary | openssl base64 -A
HTMX_SRI = "sha384-0895/pl2MU10Hqc6jd4RvrthNlDiE9U1tWmX7WRESftEDRosgxNsQG/Ze9YMRzHq"


def htmx_script_tag():
    return html.script(
        src=HTMX_URL,
        integrity=HTMX_SRI,
        crossorigin="anonymous",
    )


out = str(htmx_script_tag())
assert 'integrity="sha384-' in out
assert 'crossorigin="anonymous"' in out
```

`crossorigin="anonymous"` is required for SRI to take effect when
the script is served from another origin — without it the browser
won't expose the response to the integrity check and the script
fails to load. When you bump the htmx version, recompute the hash —
stale SRI breaks the page instantly, which is exactly what you
want.

### Lock down htmx's runtime config

htmx reads a JSON config from `<meta name="htmx-config">` (or via
`htmx.config.<key> = ...` in JS). The flags below tighten the
defaults.

<!-- name: test_htmx_config_meta -->
```python
import json
from tagz import html


HTMX_CONFIG = {
    # Only allow htmx to send requests back to the page's origin.
    # Cross-origin hx-get/hx-post are blocked.
    "selfRequestsOnly": True,
    # Refuse to evaluate hx-on:* string handlers. Default since 1.9.x;
    # be explicit anyway.
    "allowEval": False,
    # Don't auto-execute <script> tags arriving in swapped HTML. If a
    # fragment slips through with one, it sits there inert.
    "allowScriptTags": False,
    # Don't cache rendered HTML in localStorage; useful when fragments
    # may contain sensitive data.
    "historyEnabled": False,
}


def htmx_config_meta():
    return html.meta(name="htmx-config", content=json.dumps(HTMX_CONFIG))


out = str(htmx_config_meta())
# Double-quote entities are just the HTML-escape of the JSON's "
# (the browser decodes before passing the value to htmx).
assert "&quot;selfRequestsOnly&quot;: true" in out
assert "&quot;allowEval&quot;: false" in out
assert "&quot;allowScriptTags&quot;: false" in out
```

### htmx-specific knobs (quick reference)

- **`selfRequestsOnly: true`** — block cross-origin requests.
- **`allowEval: false`** — refuse to evaluate `hx-on:*` strings.
- **`allowScriptTags: false`** — don't run `<script>` tags swapped
  into the page. The default is `true`, which is the historical
  source of "I sanitised the data but htmx ran it anyway" bugs.
- **`hx-headers='{"X-CSRF-Token":"..."}'`** (per element) or
  `"globalHeaders"` in the config — pin a CSRF token onto every
  htmx request. Validate it server-side.
- **`hx-disable`** on a subtree — tell htmx to ignore everything
  inside. Useful when rendering user-controlled markup that lives
  inside a wrapper your own sanitiser owns.

The takeaway: tagz makes the **default** path safe (escape + typed
attributes). SRI + CSP + the htmx-config lockdown + CSRF are the
perimeter you draw around the response.

## Want a bigger example?

The repo ships with a working demo at
[`examples/htmx-asyncio`](https://github.com/mosquito/tagz/tree/master/examples/htmx-asyncio):
live cards for server time, client IP, PyPI metadata, a greet form,
and a stateful counter — all rendered with tagz and swapped in with
htmx. It demonstrates the pre-resolve-async-data pattern from
[Async and tagz](../explanation/async-and-tagz.md) end-to-end.
