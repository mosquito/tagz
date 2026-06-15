# Assemble a page in parts

**Problem.** You want to build a page top-down but fill in some
sections later — for instance, header now, content after a database
fetch.

**Solution.** Pass a **callable** (or a lambda) that returns the
live reference, and mutate the referenced tag freely afterwards.

<!-- name: test_assemble_in_parts -->
```python
from tagz import html, Page

content = html.div(id="content")

page = Page(
    lang="en",
    body_element=html.body(
        html.h1("Report"),
        html.hr(),
        lambda: content,        # late binding via callable
    ),
    head_elements=(html.title("Report"),),
)

# ...later, after fetching data:
content.append(html.p("First row"))
content.append(html.p("Second row"))

out = page.to_html5()
assert '<div id="content"><p>First row</p><p>Second row</p></div>' in out
```

## Why the callable?

`TagInstance.__init__` makes a defensive copy of every child tag it
receives so that the same template-tag can be reused with different
contexts. Without the lambda, the `content` you keep a reference to
and the one inside the page would be different objects — appends
would target the orphan, not the rendered tree.

Wrapping the reference in a callable defers the lookup to render
time, when the live object is read.

## Alternative: build the tree fully before wrapping in `Page`

If you don't need to mutate after `Page` construction, build the
entire tree bottom-up first:

<!-- name: test_assemble_built_first -->
```python
from tagz import html, Page

content = html.div(id="content")
content.append(html.p("Row"))

body = html.body(
    html.h1("Report"),
    content,
)

page = Page(body_element=body, head_elements=(html.title("Report"),))
out = page.to_html5()
assert '<div id="content"><p>Row</p></div>' in out
```

See [Callables and laziness](../explanation/callables-and-laziness.md)
for the full callable contract.
