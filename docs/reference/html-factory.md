# The `html` factory

The `html` object is the everyday entry point. Every attribute access
returns a class for the matching HTML element, with sensible defaults
already wired in.

## Two ways to access tags

`html.div` and `html["div"]` are equivalent. Attribute access is
ergonomic; subscript access supports hyphenated and dynamically
chosen names.

<!-- name: test_factory_access -->
```python
from tagz import html

assert html.div is html["div"]

custom = html["my-element"]("hello")
assert custom.to_string() == "<my-element>hello</my-element>"
```

## Underscores become hyphens

Python identifiers can't contain hyphens, so `tagz` rewrites
underscores in attribute names to hyphens.

<!-- name: test_factory_underscore -->
```python
from tagz import html

assert html.my_custom_tag("x").to_string() == "<my-custom-tag>x</my-custom-tag>"
```

The same rule applies to attribute keyword arguments (`data_value` →
`data-value`).

## Void elements

Void elements have no closing tag and no children. Passing children
to them raises `ValueError`.

| Element | Element | Element | Element |
| ------- | ------- | ------- | ------- |
| `area`  | `embed` | `link`  | `source`|
| `base`  | `hr`    | `meta`  | `track` |
| `br`    | `img`   | `param` | `wbr`   |
| `col`   | `input` |         |         |

<!-- name: test_factory_void -->
```python
from tagz import html

assert html.br().to_string() == "<br/>"
assert html.img(src="cat.png", alt="cat").to_string() == '<img alt="cat" src="cat.png"/>'

try:
    html.br("oops")
except ValueError:
    pass
else:
    raise AssertionError("void element accepted children")
```

## Unescaped elements

Inside `<script>` and `<style>` content is **not** HTML-escaped — JS
and CSS frequently contain `<`, `>`, and `&` characters that would
otherwise be mangled.

<!-- name: test_factory_unescaped -->
```python
from tagz import html

snippet = html.script("if (a < b && c > 0) {}")
assert snippet.to_string() == "<script>if (a < b && c > 0) {}</script>"
```

See [The escaping model](../explanation/escaping-model.md) for the
full story.

## Custom defaults

The `HTML` class accepts a `defaults` mapping that mirrors the built-
in `html` factory. Use it when you want a fresh factory with extra
tags or different defaults.

<!-- name: test_factory_custom -->
```python
from tagz import HTML

# Define a brand-new factory that treats `mathml` as unescaped.
custom = HTML({"mathml": {"__escaped__": False}})

assert custom.mathml("a < b").to_string() == "<mathml>a < b</mathml>"
```
