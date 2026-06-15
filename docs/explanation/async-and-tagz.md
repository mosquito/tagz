# Async and `tagz`

`tagz` has no async rendering API. There is no `await tag.to_html5()`,
no `aiter_chunk()`, no `aresolve()`. This is intentional. This page
explains the reasoning so the question doesn't come up again — and
walks through the pattern you should use instead.

## The recommended pattern

Resolve async data **before** building the tree. The tree itself
stays synchronous and declarative.

<!-- name: test_async_recommended -->
```python
import asyncio
from tagz import html, Page

async def fetch_user_name() -> str:
    await asyncio.sleep(0)
    return "Ada"

async def fetch_posts() -> list[str]:
    await asyncio.sleep(0)
    return ["First post", "Second post"]

async def render() -> str:
    # 1. Pull async data first — concurrently if you like.
    name, posts = await asyncio.gather(fetch_user_name(), fetch_posts())

    # 2. Build the tree from plain values.
    page = Page(
        body_element=html.body(
            html.h1(f"Hello, {name}"),
            html.ul(*(html.li(p) for p in posts)),
        ),
        head_elements=(html.title(f"{name}'s page"),),
    )

    # 3. Render synchronously.
    return page.to_html5()

assert "Hello, Ada" in asyncio.run(render())
```

## Why not an async render path?

Several design forces line up the same way.

### 1. Coroutines are one-shot

`async def f(): ...; c = f()` produces a coroutine you can only
`await` once. `tagz` calls children per-render — so an async child
would work on the first render and crash on the second.

The only way to make this safe is to **mutate** the tree on first
render, replacing the coroutine with its result. Now `str(tag)`
sometimes mutates state and sometimes doesn't, depending on whether
async children are present. That's a surprising and dangerous API.

### 2. Rendering should not do I/O

Today's mental model is dead simple: building a tag is cheap, and
rendering is CPU-only string concatenation. If render-time can `await`
arbitrary coroutines, render-time can:

- raise network errors,
- hang on a slow DB,
- take time proportional to whatever your async callable does.

You no longer know when `str(page)` will return. Worse, it may now
*time out* — and the call site usually doesn't know to handle that.

### 3. It breaks the sync API

Library users want `print(page.to_html5())` to keep working in
notebooks, scripts, and FastAPI handlers. If `tagz` adds an
async-only path, you can no longer migrate a Tag back-and-forth.
Code that took a Tag has to be re-audited for whether it might
encounter async children.

### 4. You don't get concurrency for free

A naive async render walks the tree in document order, awaiting each
async child sequentially. Total render time is the **sum** of every
await — no faster than `asyncio.gather()`-ing the same data outside
the tree. To get real concurrency you'd add a pre-resolve pass that
gathers all coroutines first… which is exactly the recommended
pattern, just shipped inside the library at the cost of all the
problems above.

## What if I really want lazy data fetching?

Use a synchronous callable that does the fetch eagerly outside the
event loop is a non-starter inside async code, but inside sync code
you can use `tagz`'s existing callable-child machinery freely — see
[Callables and laziness](callables-and-laziness.md).

If you're in async code and the data really must be lazy, write a
small helper that resolves the tree:

<!-- name: test_async_helper_pattern -->
```python
import asyncio
from tagz import html

async def resolve_async(value):
    # Helper: accept either a value or a coroutine returning a value.
    if asyncio.iscoroutine(value):
        return await value
    return value

async def build_card(user_id: int):
    name_coro = asyncio.sleep(0, result=f"user-{user_id}")
    name = await resolve_async(name_coro)
    return html.div(html.strong(name))

card = asyncio.run(build_card(7))
assert str(card) == "<div><strong>user-7</strong></div>"
```

## How-to

- [Pre-resolve async data](../how-to/prefetch-async-data.md) — the
  recipe form of the pattern above.
