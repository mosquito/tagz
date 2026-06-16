# Boolean attributes

**Problem.** HTML boolean attributes — `checked`, `disabled`,
`readonly`, `required`, `autofocus`, `hidden`, etc. — render as a
bare name with no value. You want to control them from Python with
plain `True` / `False`.

**Solution.** Pass `True` to emit the bare attribute, `False` to
remove it.

<!-- name: test_bool_attr_basic -->
```python
from tagz import html

# checked=True → bare attribute
on = html.input(type="checkbox", checked=True)
assert on.to_string() == '<input checked type="checkbox"/>'

# checked=False → attribute omitted
off = html.input(type="checkbox", checked=False)
assert off.to_string() == '<input type="checkbox"/>'
```

## Toggling at runtime

<!-- name: test_bool_attr_toggle -->
```python
from tagz import html

tag = html.button("Save", disabled=True)
assert "disabled" in tag.to_string()

tag["disabled"] = False
assert "disabled" not in tag.to_string()

tag["disabled"] = True
assert "disabled" in tag.to_string()
```

## Combining with `None` for late-binding boolean

If a callable returns `None`, that's the same as `True` — bare
attribute name. Useful when you want the attribute always present
but the value computed:

<!-- name: test_bool_attr_late -->
```python
from tagz import html

def autofocus_attr():
    return None  # always present

tag = html.input(type="text", autofocus=autofocus_attr)
assert tag.to_string() == '<input autofocus type="text"/>'
```

## See also

- [Conditional attributes with `ABSENT`](conditional-attributes-with-absent.md)
  — the inverse case (sometimes absent).
