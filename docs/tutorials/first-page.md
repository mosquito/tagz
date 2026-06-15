# Build your first page

By the end of this tutorial you'll have a complete HTML5 document
constructed entirely in Python, pretty-printed, and saved to disk.

## What you'll learn

- Building a tag tree from `html.body`, `html.head` and friends.
- Wrapping the tree in a `Page` so it ships with a DOCTYPE.
- Rendering pretty-printed output.
- Serialising the document to a file.

## Prerequisites

- Python 3.10 or later.
- `tagz` installed: ``pip install tagz`` (or ``uv add tagz``).

## Step 1 — a single element

Start in a Python REPL or a fresh script.

<!-- name: test_first_page_single -->
```python
from tagz import html

greeting = html.h1("Hello, world")
assert str(greeting) == "<h1>Hello, world</h1>"
```

Two things to notice:

- `html.h1` is a class. Calling it with positional arguments
  produces a tag instance whose children are those arguments.
- Strings are HTML-escaped automatically — try
  ``html.h1("<script>")`` and inspect the output.

## Step 2 — nesting

Tags accept other tags as children. Build a small section.

<!-- name: test_first_page_nesting -->
```python
from tagz import html

card = html.div(
    html.h2("Card"),
    html.p("Some body copy with ", html.strong("emphasis"), "."),
    classes=["card", "card-default"],
)

out = str(card)
assert '<div class="card card-default">' in out
assert "<strong>emphasis</strong>" in out
```

Keyword arguments map to attributes (with underscores converted to
hyphens). The special `classes=` keyword sets the CSS class set.

## Step 3 — wrap it in a Page

A `Page` knows about `<!DOCTYPE html>`, `<html>`, `<head>` and
`<body>`. You only have to supply head children and a body.

<!-- name: test_first_page_page -->
```python
from tagz import html, Page

page = Page(
    lang="en",
    body_element=html.body(
        html.h1("Hello"),
        html.p("This is my first ", html.code("tagz"), " page."),
    ),
    head_elements=(
        html.meta(charset="utf-8"),
        html.meta(name="viewport", content="width=device-width, initial-scale=1"),
        html.title("My first tagz page"),
    ),
)

out = page.to_html5(pretty=True)
assert out.startswith("<!doctype html>")
assert "<title>" in out
assert "Hello" in out
```

`Page.to_html5(pretty=True)` indents the output one tab per level.
Set ``pretty=False`` (the default) when you don't need readability —
it's faster.

## Step 4 — write the file

<!-- name: test_first_page_write -->
```python
from pathlib import Path
from tempfile import TemporaryDirectory
from tagz import html, Page

page = Page(
    lang="en",
    body_element=html.body(html.h1("Saved")),
    head_elements=(html.title("Saved page"),),
)

with TemporaryDirectory() as tmp:
    out_path = Path(tmp) / "page.html"
    out_path.write_text(page.to_html5(pretty=True), encoding="utf-8")
    assert out_path.exists()
    assert "Saved page" in out_path.read_text(encoding="utf-8")
```

In a real script you'd write to a fixed path:

```python
Path("dist/index.html").write_text(page.to_html5(pretty=True))
```

## Where to next?

- Want to load and modify an existing page? See
  [Parsing and modifying](parsing-and-modifying.md).
- Need to render a huge document without loading it all into memory?
  See [Stream a large document](streaming-large-doc.md).
- Reach for a specific recipe in the [How-to guides](../how-to/index.md)
  for tasks like CSS, conditional attributes, or pre-resolving async
  data.
