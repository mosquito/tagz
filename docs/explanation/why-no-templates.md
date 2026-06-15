# Why no templates?

`tagz` is built on the bet that **Python is a better template
language than Jinja2** — for a specific class of problems.

## What templates buy you

Template engines (Jinja2, Mako, Django templates) exist for one
strong reason: **a designer can edit HTML without touching Python**.
The template file looks like HTML, lives outside the codebase, and a
non-engineer can change copy or layout without breaking the program.

If that's your situation, use Jinja2. `tagz` will not help you.

## What templates cost you

When the only person editing the template is a backend engineer, the
template engine starts costing more than it gives:

- **A second syntax to learn and tool against.** `{% if %}`,
  `{{ foo|safe }}`, `{% for %}` — none of it is real Python. Your
  editor can't autocomplete it. Your type checker can't see it. Your
  refactoring tool can't rename through it.
- **Two contexts to wire together.** Every variable used in the
  template has to be passed in. Every helper has to be exposed as a
  filter or global. You're constantly translating between two
  worlds.
- **Runtime errors instead of import errors.** Misspell a variable
  name in Python — `NameError` at import. Misspell it in a template
  — silent empty string in production.
- **No type information.** The template doesn't know if `user` is a
  `User` or `None`. You discover the second case when the page
  renders weird.

## What `tagz` gives you instead

A direct mapping from Python expression to HTML element. The page is
just a function that returns a `Tag`:

<!-- name: test_why_no_templates_function -->
```python
from tagz import html, Page

def render_user_card(name: str, posts: list[str]) -> Page:
    return Page(
        body_element=html.body(
            html.h1(f"Hello, {name}"),
            html.ul(*(html.li(p) for p in posts)),
        ),
        head_elements=(html.title(f"{name}'s page"),),
    )

page = render_user_card("Ada", ["First post", "Second post"])
out = page.to_html5()
assert "Hello, Ada" in out
assert "<li>First post</li>" in out
```

You get:

- **Static checking.** `mypy` knows the shape of `posts`. Renaming
  `name` updates every call site.
- **Real Python.** Conditionals are `if/else`. Loops are `for`. Helpers
  are functions. Reuse is composition.
- **One layer.** No template/Python interface to wire up.

## When to pick what

| Need | Use |
| ---- | --- |
| Designer-edited templates | Jinja2 |
| Pages emitted by Python code only | `tagz` |
| Generating HTML emails / reports | `tagz` |
| Transforming HTML programmatically | `tagz` (with [`parse`](../reference/api.md)) |
| Embedding small HTML in another framework's response | `tagz` |
| Large static site with content authors | Hugo / Eleventy / etc. |

## Further reading

- [Architecture](architecture.md) — the class layout that makes the
  Python API feel natural.
- [Callables and laziness](callables-and-laziness.md) — the one
  template-like feature `tagz` does include, and why.
