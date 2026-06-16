# Custom tags

**Problem.** You want to emit a tag name that isn't a standard
HTML element — a Web Component, an unknown future element, or a
namespaced custom tag like `<my-card>`.

**Solution.** Just ask the `html` factory for it. Any name works.
Use an underscore in attribute-style access and `tagz` will rewrite
it to a hyphen.

<!-- name: test_custom_tag_basic -->
```python
from tagz import html

assert html.my_card("hi").to_string() == "<my-card>hi</my-card>"

# Equivalent via subscript access:
same = html["my-card"]("hi")
assert same.to_string() == "<my-card>hi</my-card>"
```

## Names with non-identifier characters

Attribute access can't express colons, dots, or other punctuation —
use the subscript form.

<!-- name: test_custom_tag_namespaced -->
```python
from tagz import html

ns = html["x:foo"]("ns content")
assert ns.to_string() == "<x:foo>ns content</x:foo>"
```

## Custom attributes

Underscores in attribute keyword names also become hyphens. This
lets you emit `data-*`, `aria-*`, and other dashed attributes
without subscripting:

<!-- name: test_custom_tag_attrs -->
```python
from tagz import html

tag = html.div(
    "hello",
    data_value="42",
    aria_label="card",
)
out = tag.to_string()
assert 'data-value="42"' in out
assert 'aria-label="card"' in out
```

## A factory with custom defaults

If you want a fresh factory where `<my-card>` is unescaped by
default (so children pass through verbatim), build a new `HTML`
instance:

<!-- name: test_custom_tag_factory -->
```python
from tagz import HTML

custom = HTML({"my-card": {"__escaped__": False}})
tag = custom.my_card("a < b")
assert tag.to_string() == "<my-card>a < b</my-card>"
```
