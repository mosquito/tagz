# Conditional attributes with `ABSENT`

**Problem.** You want an attribute to appear sometimes and disappear
other times, without two parallel branches that construct the tag
differently.

**Solution.** Set the attribute to a callable that returns
:data:`ABSENT` when you want it gone, and a value otherwise. `tagz`
omits the attribute entirely when the result is `ABSENT`.

<!-- name: test_absent_attr_basic -->
```python
from tagz import html, ABSENT

state = {"open": True}

def aria_expanded():
    return "true" if state["open"] else ABSENT

panel = html.div("...", aria_expanded=aria_expanded)
assert 'aria-expanded="true"' in panel.to_string()

state["open"] = False
assert "aria-expanded" not in panel.to_string()
```

## Why a sentinel, not `None`?

`None` is reserved for **boolean attributes** — it renders the
attribute as a bare name (`<input checked>`). If you want the
attribute removed, `ABSENT` is the explicit signal.

| Callable returns | Rendering |
| ---------------- | --------- |
| `"value"` | `attr="value"` |
| `None` | bare `attr` (boolean) |
| `ABSENT` | omitted entirely |
| `True` | bare `attr` (boolean) |
| `False` | omitted entirely |

## Static example

You can also pass `ABSENT` directly (not via a callable) — handy
when computing attributes inline:

<!-- name: test_absent_attr_static -->
```python
from tagz import html, ABSENT

def label_for(disabled: bool):
    return html.input(
        type="text",
        disabled=None if disabled else ABSENT,
    )

assert "disabled" in label_for(True).to_string()
assert "disabled" not in label_for(False).to_string()
```

## See also

- [Boolean attributes](boolean-attributes.md)
- [Callables and laziness](../explanation/callables-and-laziness.md)
