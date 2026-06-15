# Callables and laziness

`tagz` lets you put a **zero-argument callable** anywhere a child or
attribute value goes. The callable is invoked at render time, and its
return value is used in place of the callable.

That single feature replaces what a template engine calls
"expressions" — and it comes with a tight contract you should
understand.

## The contract

1. **A callable is invoked exactly once per render.** If you walk the
   same tree twice via `to_string()` or `iter_*()`, the callable runs
   twice. There is no memoisation.
2. **A callable child returning a string is escaped** (unless the
   containing tag has `_escaped=False`, like `<script>`/`<style>`).
3. **A callable child returning a `Tag` is composed as a subtree** —
   the result is rendered just like a tag passed directly.
4. **A callable attribute value is escaped with `quote=True`.** If
   the result is :data:`ABSENT`, the attribute is omitted. If it's
   `None`, the attribute is rendered as a boolean.
5. **Callables in attributes aren't expected to return tags.** If
   you do, they'll be stringified and escaped — almost certainly not
   what you wanted.

## Example: lazy children

<!-- name: test_callables_lazy_child -->
```python
from tagz import html

calls = []

def render_child():
    calls.append(1)
    return "lazy content"

tag = html.div(render_child)

# Not yet called — construction is cheap.
assert calls == []

assert str(tag) == "<div>lazy content</div>"
assert calls == [1]

# Render again — runs again.
str(tag)
assert calls == [1, 1]
```

## Example: conditional attributes

<!-- name: test_callables_conditional_attr -->
```python
from tagz import html, ABSENT

state = {"disabled": False}

def disabled_attr():
    return None if state["disabled"] else ABSENT

button = html.button("Save", disabled=disabled_attr)
assert str(button) == "<button>Save</button>"

state["disabled"] = True
assert str(button) == "<button disabled>Save</button>"
```

## Why lazy at all?

Two reasons:

- **Templates have late binding.** Jinja2 doesn't evaluate `{{ foo }}`
  until rendering. If `tagz` evaluated everything at construction,
  you couldn't build a reusable card and then fill it in.
- **Costly expressions stay costly only when rendered.** If a
  callable hits a slow path, it pays only when the tag actually
  reaches output — useful for content blocks that may be skipped by
  a parent's logic.

## Side effects are your problem

Because callables run per render, side effects compound:

<!-- name: test_callables_side_effect_warning -->
```python
from tagz import html

counter = {"n": 0}

def increment():
    counter["n"] += 1
    return str(counter["n"])

tag = html.div(increment)
assert str(tag) == "<div>1</div>"
assert str(tag) == "<div>2</div>"  # not idempotent!
```

If you need a value computed once, compute it before the tree:

<!-- name: test_callables_precompute -->
```python
from tagz import html

def expensive():
    return "result"

value = expensive()        # pay once
tag = html.div(value)      # pure data afterwards
assert str(tag) == "<div>result</div>"
assert str(tag) == "<div>result</div>"
```

## Callables and async

A callable returning a coroutine **does not work** — `tagz` will not
await it. See [Async and tagz](async-and-tagz.md) for the
recommended pattern (`await` the value before placing it in the
tree).

## Related

- [The escaping model](escaping-model.md) — exactly which call sites
  escape strings.
- How-to: [Lazy children with callables](../how-to/lazy-children-with-callables.md)
- How-to: [Conditional attributes with ABSENT](../how-to/conditional-attributes-with-absent.md)
