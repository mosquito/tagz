# Unescaped content in `<script>` and `<style>`

**Problem.** You want to put real JavaScript or CSS into a page —
content where `<`, `>`, and `&` mean something. Default HTML
escaping would mangle the code.

**Solution.** `tagz` already knows. The `<script>` and `<style>`
tags are created with escaping disabled.

<!-- name: test_unescaped_script -->
```python
from tagz import html

js = html.script("if (a < b && c > 0) console.log('<3');")
assert "<" in str(js)
assert "&lt;" not in str(js)
```

<!-- name: test_unescaped_style -->
```python
from tagz import html

css = html.style("body > .parent { color: red; }")
assert ">" in str(css)
```

## Embedding values

Because the content is unescaped, **anything** you interpolate into
a `<script>` block is part of the JavaScript program. Building a
script with user input is an XSS vector:

```text
# DANGER: user_name from request is now executable JavaScript.
html.script(f"console.log('hello {user_name}');")
```

The safe pattern is to serialise the data with `json.dumps` and let
JSON encoding handle the escaping:

<!-- name: test_unescaped_safe -->
```python
import json
from tagz import html

payload = {"name": "Ada"}
tag = html.script(f"window.__data__ = {json.dumps(payload)};")
assert "window.__data__" in str(tag)
assert '"name": "Ada"' in str(tag)
```

For especially tricky payloads (containing `</script>` substrings),
either base64-encode the data or split the tag boundary outside
Python — a topic well covered elsewhere.

## Making other tags unescaped

If you need a custom element treated like `<script>`, see
[Custom tags](custom-tags.md) — pass `__escaped__: False` to a fresh
`HTML` factory.
