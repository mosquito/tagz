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

This part needs `aiohttp` installed (`pip install aiohttp`); it's
shown as plain code rather than executed in the test suite.

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

if __name__ == "__main__":
    web.run_app(app, host="127.0.0.1", port=8080)
```

That's the whole app. Open the page, click the button, the button
disappears and the `<span>` takes its place.

## Want a bigger example?

The repo ships with a working demo at
[`examples/htmx-asyncio`](https://github.com/mosquito/tagz/tree/master/examples/htmx-asyncio):
three live cards (server time, client IP, PyPI metadata) rendered
with tagz and swapped in with htmx. It demonstrates the
pre-resolve-async-data pattern from
[Async and tagz](../explanation/async-and-tagz.md) end-to-end.
