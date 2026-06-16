# Parse and modify existing HTML

Some workflows start with an HTML document already on disk — a
template you downloaded, output from another tool, scraped content
you want to clean up. `tagz` ships with a parser that turns HTML
into the same `Tag` objects you'd build by hand, so you can walk and
mutate the tree in pure Python.

## What you'll learn

- Reading HTML into a `Tag` / `Fragment` / `Page` object.
- Walking children to find a specific node.
- Replacing and appending nodes.
- Re-serialising the modified tree.

## Step 1 — read a snippet

`parse()` accepts any HTML string. Depending on the input it returns
a single `Tag`, a `Fragment` (for multiple top-level elements), or a
`Page` (for a full `<html>` document).

<!-- name: test_parse_single -->
```python
from tagz import parse, Tag

tag = parse("<div><p>Hello</p></div>")
assert isinstance(tag, Tag)
assert tag.name == "div"
assert len(tag.children) == 1
assert tag.children[0].name == "p"
```

## Step 2 — read a multi-element snippet

<!-- name: test_parse_fragment -->
```python
from tagz import parse, Fragment

frag = parse("<p>One</p><p>Two</p>")
assert isinstance(frag, Fragment)
assert len(frag.children) == 2
assert frag.to_string() == "<p>One</p><p>Two</p>"
```

## Step 3 — read a full document

When the input contains `<html>`, `parse()` returns a `Page` —
ready for round-tripping with the original DOCTYPE preserved.

<!-- name: test_parse_page -->
```python
from tagz import parse, Page

source = """<!DOCTYPE html>
<html lang="en">
<head><title>Demo</title></head>
<body><h1>Welcome</h1></body>
</html>"""

result = parse(source)
assert isinstance(result, Page)
assert "Welcome" in result.body.to_string()
assert "Demo" in result.head.to_string()

out = result.to_html5()
assert out.startswith("<!DOCTYPE html>")
```

## Step 4 — walk the tree

A `Tag.children` list contains tags and strings in document order.
You can walk it recursively or just inspect what you need.

<!-- name: test_parse_walk -->
```python
from tagz import parse, Tag

doc = parse("<div><h1>Title</h1><p>Body</p><p>More</p></div>")
assert isinstance(doc, Tag)

# Find the first paragraph.
paragraphs = [c for c in doc.children if isinstance(c, Tag) and c.name == "p"]
assert len(paragraphs) == 2
assert paragraphs[0].children == ["Body"]
```

## Step 5 — modify

Tags are mutable — replace children by index, append to lists,
update attributes via item access.

<!-- name: test_parse_modify -->
```python
from tagz import parse, html, Tag

doc = parse("<article><h1>Old Title</h1><p>Body</p></article>")
assert isinstance(doc, Tag)

# Replace the heading.
doc.children[0] = html.h1("New Title", classes=["accent"])

# Add a footer.
doc.append(html.footer("Updated"))

out = doc.to_string()
assert "New Title" in out
assert "Updated" in out
assert 'class="accent"' in out
```

## Step 6 — round-trip a document

Serialise the modified tree back to HTML. For a full document, the
rendered tree lives at ``page.html`` — that is the tag that
`to_html5()` actually serialises. ``page.head`` and ``page.body``
are the originals you passed in (or the parser produced), but
`Page` keeps independent copies inside ``page.html`` for rendering.
To modify the rendered output, mutate ``page.html.children``
directly.

<!-- name: test_parse_roundtrip -->
```python
from tagz import parse, Page, Tag

source = "<!DOCTYPE html><html><head><title>x</title></head><body><h1>x</h1></body></html>"
page = parse(source)
assert isinstance(page, Page)

# Walk into the rendered tree to find the <title>.
head_tag = next(c for c in page.html.children if isinstance(c, Tag) and c.name == "head")
title_tag = next(c for c in head_tag.children if isinstance(c, Tag) and c.name == "title")
title_tag.children = ["Updated"]

out = page.to_html5()
assert "<title>Updated</title>" in out
```

```{tip}
The split between ``page.head`` / ``page.body`` and the rendered
tree under ``page.html`` is a quirk worth knowing — it lets `Page`
construction be cheap (no need to re-link parents), at the cost of
the rendered tree being a copy. When in doubt, work through
``page.html``.
```

## Where to next?

- Need to ingest a streaming source? `parse()` requires the full
  string in memory; for very large inputs use the standard library's
  [`html.parser`](https://docs.python.org/3/library/html.parser.html)
  directly.
- For a list of attributes and methods on the parsed objects, see
  the [API reference](../reference/api.md).
