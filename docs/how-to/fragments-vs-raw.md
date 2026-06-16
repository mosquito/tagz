# Fragments vs Raw

**Problem.** You want to emit multiple elements without a wrapper, or
splice in pre-rendered HTML — and you're not sure whether to use
`Fragment` or `Raw`.

**Solution.** Use `Fragment` when the children are `tagz` objects.
Use `Raw` only when you have a trusted, already-rendered HTML string
that must pass through verbatim.

## `Fragment` — wrapper-less group

<!-- name: test_fragment_basic -->
```python
from tagz import html, Fragment

# A function returns multiple top-level elements:
def render_header():
    return Fragment(
        html.h1("Title"),
        html.h2("Subtitle"),
    )

assert render_header().to_string() == "<h1>Title</h1><h2>Subtitle</h2>"
```

Fragments compose: pass one as a child of another tag and it renders
its children inline.

<!-- name: test_fragment_in_tag -->
```python
from tagz import html, Fragment

page = html.body(
    html.header("Top"),
    Fragment(html.p("A"), html.p("B")),
    html.footer("Bottom"),
)
assert page.to_string() == "<body><header>Top</header><p>A</p><p>B</p><footer>Bottom</footer></body>"
```

## `Raw` — verbatim HTML

`Raw` takes a single string and emits it **without** escaping. Use
it for pre-rendered HTML you control, never for user input.

<!-- name: test_raw_basic -->
```python
from tagz import html, Raw

# Trusted HTML fragment from elsewhere:
snippet = "<em>fast</em> &amp; safe"
container = html.p("Status: ", Raw(snippet))
assert container.to_string() == "<p>Status: <em>fast</em> &amp; safe</p>"
```

## Which one do I want?

| You have... | Use |
| ----------- | --- |
| Several `tagz` objects to group | `Fragment` |
| A string you trust to be valid HTML | `Raw` |
| A string that came from a user | **neither** — pass it as a normal child so it gets escaped |
| Output from another renderer (Markdown, Jinja) you trust | `Raw` |

## XSS warning

```{warning}
`Raw` disables all escaping. If the string contains anything derived
from user input — directly or indirectly — you have an XSS vector.
Sanitise upstream with a library like
[`bleach`](https://github.com/mozilla/bleach) before wrapping in
`Raw`.
```

See [The escaping model](../explanation/escaping-model.md) for the
full story.
