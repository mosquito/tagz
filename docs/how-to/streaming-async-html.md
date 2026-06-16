# Stream HTML asynchronously

**Problem.** You're inside an async handler. The page depends on
data you must `await` — but you want to start sending bytes to the
client before every fetch completes.

**Solution.** Build the tree with `tagz.aio.html` and stream it
via `tag.iter_chunk()`. The renderer emits HTML in document order
and awaits async values inline as it reaches them.

## Single string vs streaming

For small pages, `await page.to_html5()` produces the full string —
exactly like `to_html5()` does in sync `tagz`.

<!-- name: async test_streaming_async_full_string -->
```python
from tagz.aio import html, Page

async def fetch_name():
    return "Ada"

page = Page(
    lang="en",
    body_element=html.body(html.h1(fetch_name())),
    head_elements=(html.title("Demo"),),
)
out = await page.to_html5()
assert "Ada" in out and "<!doctype html>" in out
```

For large pages or slow data, stream the bytes as they're produced.

<!-- name: async test_streaming_async_chunks -->
```python
from tagz.aio import html

async def fetch_name():
    return "Ada"

tag = html.div(html.h1(fetch_name()), html.p("Welcome!"))
out = []
async for chunk in tag.iter_chunk(chunk_size=16):
    out.append(chunk)
assert "".join(out) == "<div><h1>Ada</h1><p>Welcome!</p></div>"
```

## Concurrent fetches with `asyncio.Task`

The renderer awaits in document order. To overlap fetches, start
them as `asyncio.Task` *before* placing them in the tree.

<!-- name: async test_streaming_async_concurrent -->
```python
import asyncio, time
from tagz.aio import html

async def slow(label, delay=0.05):
    await asyncio.sleep(delay)
    return label

t0 = time.perf_counter()
# Three tasks fired before render — they overlap.
tasks = [asyncio.create_task(slow(f"t{i}")) for i in range(3)]
tag = html.div(*(html.p(t) for t in tasks))
out = await tag.to_string()
elapsed = time.perf_counter() - t0

assert "t0" in out and "t2" in out
assert elapsed < 0.15      # three × 50ms overlapped, not summed
```

## Async iterables for unbounded streams

If you don't know how many items you'll emit, yield them from an
async generator.

<!-- name: async test_streaming_async_iterable -->
```python
import asyncio
from tagz.aio import html

async def rows():
    for i in range(3):
        await asyncio.sleep(0)
        yield html.tr(html.td(f"row {i}"))

table = html.table(rows())
out = await table.to_string()
assert out == (
    "<table>"
    "<tr><td>row 0</td></tr>"
    "<tr><td>row 1</td></tr>"
    "<tr><td>row 2</td></tr>"
    "</table>"
)
```

## aiohttp `StreamResponse`

Feed chunks straight into the response writer. aiohttp will push
each chunk to the client as it arrives.

```python
from aiohttp import web
from tagz.aio import html, Page

async def render(request: web.Request) -> web.StreamResponse:
    page = Page(
        lang="en",
        body_element=html.body(html.h1(fetch_name())),
        head_elements=(html.title("Demo"),),
    )

    resp = web.StreamResponse(headers={"Content-Type": "text/html; charset=utf-8"})
    await resp.prepare(request)
    async for chunk in page.html.iter_chunk(chunk_size=4096):
        await resp.write(chunk.encode("utf-8"))
    await resp.write_eof()
    return resp
```

## Starlette / FastAPI `StreamingResponse`

`StreamingResponse` accepts an async generator; pass `iter_chunk`
directly.

```python
from starlette.responses import StreamingResponse
from tagz.aio import html, Page

async def render():
    page = Page(body_element=html.body(html.h1(fetch_name())))

    async def stream():
        async for chunk in page.html.iter_chunk():
            yield chunk.encode("utf-8")

    return StreamingResponse(stream(), media_type="text/html")
```

## See also

- [Async and `tagz`](../explanation/async-and-tagz.md) — the design
  rationale and constraints.
- [Pre-resolve async data](prefetch-async-data.md) — when you'd
  rather resolve everything outside the tree and render
  synchronously.
- [Rendering and streaming](../explanation/rendering-and-streaming.md)
  for the sync streaming model.
