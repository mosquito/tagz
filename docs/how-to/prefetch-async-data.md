# Pre-resolve async data

**Problem.** You're rendering a page from an async handler and the
content depends on database/API calls. You'd like the tree to be
declarative, not a chain of `await`s.

**Solution.** Resolve all async data first — concurrently with
`asyncio.gather()` — and build the tree from plain values. The
render itself stays synchronous.

<!-- name: test_prefetch_async_basic -->
```python
import asyncio
from tagz import html, Page

async def fetch_user():
    await asyncio.sleep(0)
    return {"name": "Ada", "email": "ada@example.com"}

async def fetch_posts():
    await asyncio.sleep(0)
    return [{"title": "First"}, {"title": "Second"}]

async def render():
    user, posts = await asyncio.gather(fetch_user(), fetch_posts())

    return Page(
        body_element=html.body(
            html.h1(user["name"]),
            html.p(user["email"]),
            html.ul(*(html.li(p["title"]) for p in posts)),
        ),
        head_elements=(html.title(user["name"]),),
    ).to_html5()

out = asyncio.run(render())
assert "Ada" in out
assert "ada@example.com" in out
assert "<li>First</li>" in out
```

## Why not a callable returning a coroutine?

A callable child runs every render; a coroutine can only be awaited
once. Putting an `async` function (or its coroutine) into the tree
will *not* work — `tagz` doesn't `await` anything.

```python
# NOT supported:
html.div(fetch_user)         # callable returning coroutine
html.div(fetch_user())       # coroutine object
```

See [Async and tagz](../explanation/async-and-tagz.md) for the
design discussion.

## Pattern with FastAPI

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from tagz import html, Page

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def index():
    user, posts = await asyncio.gather(fetch_user(), fetch_posts())
    return Page(
        body_element=html.body(
            html.h1(user["name"]),
            html.ul(*(html.li(p["title"]) for p in posts)),
        ),
    ).to_html5()
```

(Not asserted to keep FastAPI out of the test deps.)
