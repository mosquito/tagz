# Stream HTML to a socket

**Problem.** You want to send a large HTML response without building
the entire string in memory.

**Solution.** Use `Tag.iter_chunk(size)` to produce fixed-size pieces
and write each piece into the socket as it arrives.

<!-- name: test_stream_to_socket_bytes -->
```python
from io import BytesIO
from tagz import html

# Pretend this is a network socket.
sink = BytesIO()

page = html.div(*[html.p(f"row {i}") for i in range(500)])

for chunk in page.iter_chunk(chunk_size=4096):
    sink.write(chunk.encode("utf-8"))

# Reassembled bytes match the full render.
assert sink.getvalue().decode("utf-8") == page.to_string()
```

## Async sockets (asyncio)

The render itself stays synchronous; you only need `await` for the
write. `iter_chunk` returns a regular iterator, so:

<!-- name: test_stream_to_socket_async -->
```python
import asyncio
from tagz import html

async def write_to(stream, page, chunk_size=4096):
    for chunk in page.iter_chunk(chunk_size=chunk_size):
        await stream.drain() if hasattr(stream, "drain") else None
        stream.write(chunk.encode("utf-8"))

# Fake async stream
class FakeStream:
    def __init__(self):
        self.buf = bytearray()
    def write(self, b): self.buf.extend(b)

async def main():
    page = html.div(html.p("hello"))
    stream = FakeStream()
    await write_to(stream, page)
    return bytes(stream.buf)

assert asyncio.run(main()) == b"<div><p>hello</p></div>"
```

## ASGI / Starlette / FastAPI

Return a `StreamingResponse` that wraps `iter_chunk`:

```python
from fastapi.responses import StreamingResponse
from tagz import html

@app.get("/big")
def big():
    page = html.div(*[html.p(f"r{i}") for i in range(10_000)])
    return StreamingResponse(
        (chunk.encode("utf-8") for chunk in page.iter_chunk(chunk_size=8192)),
        media_type="text/html",
    )
```

(Not asserted because we don't want a FastAPI dependency in the
test suite.)

## See also

- [Rendering and streaming](../explanation/rendering-and-streaming.md) —
  the trade-offs between `iter_string`, `iter_lines`, `iter_chunk`.
