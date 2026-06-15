# Stream a large document

When you generate a table with ten thousand rows, the rendered HTML
is megabytes. Holding both the tag tree and the full output string
in memory at once is wasteful — and unnecessary, because `tagz`
renders incrementally.

In this tutorial you'll build a 10,000-row table, stream it to disk,
and inspect the difference between buffered and streamed output.

## What you'll learn

- Constructing a tag tree with thousands of children.
- Using `iter_chunk` to write fixed-size pieces.
- Using `iter_lines` to write one HTML line per output line.
- Verifying the reassembled output matches the in-memory render.

## Step 1 — build the tree

<!-- name: test_streaming_build -->
```python
from tagz import html

def build_table(n: int):
    header = html.tr(html.th("id"), html.th("name"))
    rows = [
        html.tr(html.td(str(i)), html.td(f"name-{i}"))
        for i in range(n)
    ]
    return html.table(header, *rows)

table = build_table(1_000)
assert len(table.children) == 1_001  # header + rows
```

(Use 10,000 in real life — we use 1,000 here so the test stays
fast.)

## Step 2 — write with `iter_chunk`

`iter_chunk(size)` yields strings of approximately `size`
characters. Write each chunk straight into a file handle without
ever building the full string.

<!-- name: test_streaming_chunk -->
```python
from pathlib import Path
from tempfile import TemporaryDirectory
from tagz import html

table = html.table(*(html.tr(html.td(f"row {i}")) for i in range(500)))

with TemporaryDirectory() as tmp:
    out = Path(tmp) / "table.html"
    with out.open("w", encoding="utf-8") as f:
        for chunk in table.iter_chunk(chunk_size=8192):
            f.write(chunk)

    # Verify by reassembling.
    assert out.read_text(encoding="utf-8") == table.to_string()
```

## Step 3 — write with `iter_lines`

`iter_lines` yields one line at a time, with no trailing newline,
and always indents pretty-print style. Useful when downstream tools
want line-oriented input.

<!-- name: test_streaming_lines -->
```python
from io import StringIO
from tagz import html

tag = html.div(html.p("a"), html.p("b"))

sink = StringIO()
for line in tag.iter_lines():
    sink.write(line + "\n")

assert sink.getvalue() == "<div>\n\t<p>\n\t\ta\n\t</p>\n\t<p>\n\t\tb\n\t</p>\n</div>\n"
```

## Step 4 — measure (optional)

Run the build with a profiler if you want hard numbers. The
takeaway: `iter_chunk` holds at most one chunk in memory at a time,
whereas `to_string()` allocates the full HTML in one shot. On a
10,000-row table that difference is megabytes.

## Common pitfalls

- **Don't reassemble chunks just to check.** Once you're streaming,
  passing the chunks to a `str.join` and comparing to `to_string()`
  in tests is fine. In production it defeats the purpose.
- **`iter_lines` is always pretty.** If you don't want indentation,
  use `iter_chunk` instead.

## Where to next?

- For socket-specific patterns (ASGI, asyncio, FastAPI) see
  [Stream HTML to a socket](../how-to/stream-to-socket.md).
- For a deeper look at how the three iter methods differ, read
  [Rendering and streaming](../explanation/rendering-and-streaming.md).
