# The escaping model

`tagz` is **secure by default**: every string you put into the tree
is HTML-escaped before reaching the output, with two well-defined
exceptions. Understanding *where* and *when* escaping happens is the
key to using the library safely.

## Where `html.escape()` is called

There are four call sites in the rendering pipeline:

1. **`Tag.append(child)`** — when `child` is a string and the tag's
   `_escaped` flag is `True`, the string is escaped before being
   stored. The same applies to all positional children passed to the
   constructor.
2. **Attribute values** — `Tag._format_attributes()` escapes every
   value with `quote=True` (so `"` becomes `&quot;`) at render
   time.
3. **Callable results** — when a callable child returns a string,
   it is escaped before being concatenated. When a callable
   attribute value returns a string, it goes through the attribute
   escape path.
4. **Class names** — written and read through the `classes`
   property, which escapes each token with `quote=True` on assign.

Net effect: there is no path by which an untrusted string can reach
the output unescaped, **except** for the two intentional exceptions
below.

## The two exceptions

### `<script>` and `<style>`

These elements take JavaScript and CSS respectively, where `<` and
`>` are common operators. Escaping them would break the code. So
`tagz` creates the `script` and `style` tags with `_escaped=False`:

<!-- name: test_escape_script_style -->
```python
from tagz import html

# Inside script/style: NOT escaped.
js = html.script("if (a < b) console.log('<3');")
assert "<" in js.to_string()
assert "&lt;" not in js.to_string()

css = html.style("body > .foo { color: red; }")
assert ">" in css.to_string()
```

Inside these tags, **you** are responsible for the content. If you
interpolate user input into a `<script>`, you have just built an XSS
vector.

### The `Raw` class

`Raw("<b>literal</b>")` deliberately disables escaping. It exists
for pre-rendered HTML fragments you trust.

<!-- name: test_escape_raw -->
```python
from tagz import Raw, html

snippet = Raw("<em>verbatim</em>")
container = html.div(snippet)
assert container.to_string() == "<div><em>verbatim</em></div>"
```

Treat `Raw` exactly like `dangerouslySetInnerHTML` in React: every
use site is a potential XSS bug; review them.

## Boolean attributes and `ABSENT`

Two non-escaping pieces of attribute behaviour are worth knowing:

- ``attr=True`` renders the attribute name with no value
  (`<input checked>`). ``attr=False`` removes it.
- ``attr=ABSENT`` (or a callable returning :data:`ABSENT`) removes
  the attribute. Useful for conditional rendering — the attribute
  either appears or it doesn't.

<!-- name: test_escape_bool_absent -->
```python
from tagz import html, ABSENT

# Boolean: present
on = html.input(type="checkbox", checked=True)
assert "checked" in on.to_string()
assert 'checked="' not in on.to_string()  # no value

# Boolean: absent
off = html.input(type="checkbox", checked=False)
assert "checked" not in off.to_string()

# ABSENT: conditional via callable
def maybe_disabled(banned: bool):
    return None if banned else ABSENT

tag = html.input(type="text", disabled=lambda: maybe_disabled(False))
assert "disabled" not in tag.to_string()
```

## What `tagz` does not protect against

- **Injecting unsafe `href` schemes** — `tagz` does not validate
  URLs. ``html.a(href="javascript:alert(1)", "click")`` will
  faithfully render that anchor. Validate URLs upstream.
- **`Raw` or `<script>` content** — see above. Both are opt-in
  escape hatches.
- **Server-side template injection between tags** — `tagz` is the
  template layer; if you're concatenating its output with another
  templating system that re-escapes, you may double-escape.

## Cross-references

- [The `html` factory](../reference/html-factory.md) lists the
  exact set of unescaped elements.
- [Callables and laziness](callables-and-laziness.md) — when
  callable-returned strings get escaped, and when they don't.
