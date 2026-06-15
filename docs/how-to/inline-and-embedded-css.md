# Inline and embedded CSS

**Problem.** You want to attach CSS to a tag — either as an inline
`style=` attribute, or as a `<style>` block in the page head.

**Solution.** Use the :class:`Style` helper for declarations and
:class:`StyleSheet` for rulesets.

## Inline `style=`

`Style(...)` stringifies to `key: value; key: value;` form. Pass it
as an attribute value; `tagz` will render the declarations.

<!-- name: test_css_inline -->
```python
from tagz import html, Style

box = html.div(
    "content",
    style=Style(
        padding="0.5rem",
        background_color="#eef",   # underscores → hyphens
        border="1px solid #999",
    ),
)
out = str(box)
assert 'style="' in out
assert "padding: 0.5rem;" in out
assert "background-color: #eef;" in out
```

## A `<style>` block with a `StyleSheet`

`StyleSheet({selector: Style(...)})` renders the rulesets. Tuple
keys group selectors.

<!-- name: test_css_stylesheet -->
```python
from tagz import html, Style, StyleSheet

block = html.style(StyleSheet({
    "body": Style(margin="0", padding="0"),
    (".btn", ".btn-primary"): Style(border_radius="4px"),
}))

rendered = str(block)
assert "body {margin: 0; padding: 0;}" in rendered
assert ".btn, .btn-primary {border-radius: 4px;}" in rendered
```

Note that `<style>` content is rendered unescaped, so characters
like `>` (used in selectors like `.parent > .child`) survive
untouched.

## Putting it together

<!-- name: test_css_in_page -->
```python
from tagz import html, Page, Style, StyleSheet

page = Page(
    body_element=html.body(
        html.h1("Hi", style=Style(color="red")),
    ),
    head_elements=(
        html.title("css demo"),
        html.style(StyleSheet({
            "body": Style(font_family="system-ui"),
        })),
    ),
)
out = page.to_html5()
assert 'style="color: red;"' in out
assert "body {font-family: system-ui;}" in out
```
