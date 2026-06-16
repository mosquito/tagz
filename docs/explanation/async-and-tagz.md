# Async and `tagz`

`tagz` ships in two flavours behind two import lines.

- **`tagz`** — the core, sync-only module. Tree construction is sync,
  rendering is sync, no `asyncio` import anywhere. Minimal pip-install.
- **`tagz.aio`** — the async mirror. Same symbol names (`html`,
  `Page`, `Fragment`, `Raw`, `Tag`, `Style`, `StyleSheet`, `parse`, …),
  same construction semantics, but every render method is `async`.
  Children and attributes may additionally be coroutines, awaitables,
  async-def functions, and async iterables.

Migration is mechanical: change the import line and add `await` /
`async for` at the render call sites.

<!-- name: async test_async_explainer_mirror -->
```python
# Sync — exactly as before
from tagz import html as sync_html, Page as SyncPage
page = SyncPage(body_element=sync_html.body(sync_html.h1("Hi")))
print(page.to_html5())

# Async — same shape, different import
from tagz.aio import html, Page

async def fetch_name():
    return "Ada"

page = Page(body_element=html.body(html.h1(fetch_name())))
out = await page.to_html5()
assert "<!doctype html>" in out
assert "Ada" in out
```

## What counts as an async value

In the async build, `children` and attribute `value`s may also be:

- a **coroutine object** (`fetch_user()`) — one-shot, awaited inline;
- an arbitrary **awaitable** (`asyncio.Future`, `asyncio.Task`,
  custom `__await__`);
- an **async-def function** (`fetch_user`) — re-callable across
  renders, recommended for trees you render more than once;
- an **async iterable** (`async def gen(): yield ...`) — items
  rendered in iteration order, each may itself be async.

The renderer materialises these recursively: an async value that
resolves to another async value gets awaited again, until a concrete
`Tag` / `str` falls out.

## Re-render and one-shot coroutines

Coroutine objects can only be awaited once. The first render exhausts
them; the second render surfaces a clear error:

<!-- name: async test_async_explainer_one_shot -->
```python
import pytest
from tagz.aio import html

async def fetch_name():
    return "Ada"

tag = html.div(fetch_name())   # raw coroutine — one-shot
await tag.to_string()          # ok

with pytest.raises(RuntimeError, match="already awaited"):
    await tag.to_string()      # boom

# Pass the function itself for trees that render more than once:
tag = html.div(fetch_name)
out1 = await tag.to_string()
out2 = await tag.to_string()
assert out1 == out2 == "<div>Ada</div>"
```

## Concurrency

The async renderer awaits in **document order** without spawning
background tasks. Total render time is the sum of all `await`s along
the way.

If you want sibling fetches to overlap, **start the tasks yourself**
before placing them in the tree. `asyncio.Task` is an awaitable, so
the renderer is happy to consume it — by the time the renderer
reaches the task, the work is usually already done.

<!-- name: async test_async_explainer_concurrent -->
```python
import asyncio, time
from tagz.aio import html

async def slow(label, delay=0.05):
    await asyncio.sleep(delay)
    return label

t0 = time.perf_counter()
# Three Tasks running concurrently, then handed to the renderer.
tasks = [asyncio.create_task(slow(f"t{i}")) for i in range(3)]
tag = html.div(*(html.p(t) for t in tasks))
out = await tag.to_string()
elapsed = time.perf_counter() - t0

assert "t0" in out and "t2" in out
assert elapsed < 0.15   # three × 50ms overlapped
```

Putting the concurrency primitive in the user's hands keeps the
library's mental model honest: rendering is just I/O on the values
you put in. If you need parallel fetches, you ask for them
explicitly.

## Mixing sync and async trees

A `tagz.aio.html.div(...)` may contain plain `tagz.html.span(...)`
children — the async renderer recurses through them as into any
sync subtree. The reverse — putting an async tag inside a sync tag
and calling sync `str(tag)` — produces an unawaited coroutine in the
output, which is virtually always a bug. Build the root with
`tagz.aio` whenever any branch may contain async values.

## What's deliberately not in the box

- **No magic eager scheduling** of children when the tree is built.
  Coroutines only run when the renderer reaches them.
- **No two-pass prefetch** (`tag.aresolve()` and similar). The
  streaming-in-document-order model is the only render mode.
- **No `__await__` on `Tag`**. The render methods are explicit:
  `to_string`, `to_html5`, `iter_chunk`, `iter_lines`, `iter_string`.

## Where to next?

- [Stream HTML to a socket asynchronously](../how-to/streaming-async-html.md) —
  the recipe form.
- [Pre-resolve async data](../how-to/prefetch-async-data.md) — the
  earlier pattern (resolve `await` outside the tree) still works and
  is sometimes the right tool.
