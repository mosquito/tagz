# Rendering and streaming

`tagz` offers four ways to turn a tree into a string. They all produce
the same HTML; they differ in **how the output reaches you**.

## The four entry points

| Method | Returns | Buffering | Pretty mode | Picks units of |
| ------ | ------- | --------- | ----------- | -------------- |
| `to_string()` | full `str` | buffers everything | optional | — |
| `iter_string()` | `Iterator[str]` | no buffering | optional | small fragments |
| `iter_lines()` | `Iterator[str]` | per-line accumulator | always pretty | lines (no `\n`) |
| `iter_chunk(size)` | `Iterator[str]` | per-chunk accumulator | optional | ~fixed-size chunks |

All four share the same internal generator (`_to_string`), so output
is identical byte-for-byte modulo formatting and chunk boundaries.

## When to use which

**Use `to_string()`** when the page is small (kilobytes), you want
the full document in memory, and you're going to write it out in one
go.

<!-- name: test_render_to_string -->
```python
from tagz import html

out = html.div(html.p("Hello")).to_string()
assert out == "<div><p>Hello</p></div>"
```

**Use `iter_lines()`** for human-readable streaming output —
log files, server-sent events, files where downstream tools expect
line-oriented input.

<!-- name: test_render_iter_lines -->
```python
from tagz import html

tree = html.div(html.p("a"), html.p("b"))
lines = list(tree.iter_lines())
assert lines[0] == "<div>"
assert lines[-1] == "</div>"
assert all("\n" not in line for line in lines)
```

**Use `iter_chunk(size)`** when you're piping into a network socket
or a buffered writer that wants pages of a known size. The chunk
boundary is byte-position-based; lines may split mid-content.

<!-- name: test_render_iter_chunk -->
```python
from tagz import html

tree = html.div(*[html.p(f"item {i}") for i in range(20)])
chunks = list(tree.iter_chunk(chunk_size=64))

# Reassembly is exact.
assert "".join(chunks) == tree.to_string()
# All but the last chunk are at the requested size.
for chunk in chunks[:-1]:
    assert len(chunk) == 64
```

**Use `iter_string()`** when you want every fragment as it is
produced — useful in tests, for hand-rolled buffering, or to feed a
write loop that does its own framing.

## What does `pretty=True` actually do?

It inserts indentation (one tab per nesting level by default) and a
newline after each open tag and between siblings. It does **not**
collapse whitespace inside text nodes — your strings come through
unchanged.

Importantly: pretty mode adds an indent **between text and the
surrounding tags**, so a `<p>Hello</p>` in pretty mode becomes:

```
<p>
    Hello
</p>
```

If that's not what you want, use `pretty=False` (the default).

## Why a generator, not a string?

Two reasons:

- **Memory.** A document with 10,000 `<tr>` rows fits in memory as a
  tree but the rendered HTML is megabytes. Streaming avoids holding
  both at once.
- **Backpressure.** When you write into a socket, the OS may slow
  you down. With a generator you produce HTML at exactly the rate
  the downstream consumes it.

## Lazy evaluation

Callable children are evaluated **inside** the render loop, not at
tree-construction time. That's a deliberate design choice — see
[Callables and laziness](callables-and-laziness.md).

## How-to recipes

- [Stream HTML to a socket](../how-to/stream-to-socket.md)
- [Convert a CSV to an HTML table](../how-to/csv-to-html-table.md)
