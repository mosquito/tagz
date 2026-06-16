# Pre-resolve async data

**Problem.** You're rendering a page from an async handler and the
content depends on database/API calls. You'd like the tree to be
declarative, not a chain of `await`s.

**Solution.** Resolve all async data first — concurrently with
`asyncio.gather()` — and build the tree from plain values. The
render itself stays synchronous.

<!-- name: async test_prefetch_async_basic -->
```python
import asyncio
from tagz import html, Page

async def fetch_user():
    return {"name": "Ada", "email": "ada@example.com"}

async def fetch_posts():
    return [{"title": "First"}, {"title": "Second"}]

user, posts = await asyncio.gather(fetch_user(), fetch_posts())

out = Page(
    body_element=html.body(
        html.h1(user["name"]),
        html.p(user["email"]),
        html.ul(*(html.li(p["title"]) for p in posts)),
    ),
    head_elements=(html.title(user["name"]),),
).to_html5()

assert "Ada" in out
assert "ada@example.com" in out
assert "<li>First</li>" in out
```

## When to pre-resolve vs use `tagz.aio`

Both patterns are supported.

- **Pre-resolve outside the tree** (this page): you await everything
  before construction; the tree itself is plain data; the render is
  sync. Simplest mental model. Best when fetches are few and you
  already know exactly which ones you need.
- **`tagz.aio`** (different import line): coroutines, awaitables,
  async functions, and async iterables can live directly inside
  `children` and attribute values. The render becomes `await`-able
  and can be streamed via `iter_chunk`. Best when components want to
  own their own data lookups, or when you want to stream bytes
  before every fetch has completed.

For the `tagz.aio` recipe, see
[Stream HTML asynchronously](streaming-async-html.md). For the
design discussion, see
[Async and tagz](../explanation/async-and-tagz.md).

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
