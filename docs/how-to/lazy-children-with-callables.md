# Lazy children with callables

**Problem.** You want to defer producing a child until render time —
maybe the value depends on state that changes, or the computation is
expensive and you don't always render.

**Solution.** Pass a zero-argument callable as a child. `tagz`
invokes it once per render and uses its return value in place.

## A string-returning callable

<!-- name: test_lazy_string -->
```python
from tagz import html

now = {"value": "first"}

tag = html.div(lambda: now["value"])

assert str(tag) == "<div>first</div>"
now["value"] = "second"
assert str(tag) == "<div>second</div>"
```

## A tag-returning callable

<!-- name: test_lazy_tag -->
```python
from tagz import html

def card():
    return html.div(html.h2("Title"), html.p("body"), classes=["card"])

container = html.section(card)
assert "<h2>Title</h2>" in str(container)
```

## Useful with `functools.partial`

<!-- name: test_lazy_partial -->
```python
from functools import partial
from tagz import html

def fmt(value, prefix):
    return f"{prefix}{value}"

row = html.div(
    partial(fmt, value=42, prefix="#"),
)
assert str(row) == "<div>#42</div>"
```

## Things to remember

- The callable runs **once per render**. Two `str(tag)` calls = two
  invocations. Side effects compound.
- A callable returning a string is HTML-escaped (unless inside
  `<script>`/`<style>`).
- A callable returning a coroutine is **not** awaited — see
  [Async and tagz](../explanation/async-and-tagz.md).

See [Callables and laziness](../explanation/callables-and-laziness.md)
for the full contract.
