# tagz

A lightweight, type-safe Python library for building and parsing HTML
documents programmatically — no templates, no DSL, just Python objects
that map directly to HTML elements.

```{toctree}
:hidden:
:maxdepth: 2

tutorials/index
how-to/index
reference/index
explanation/index
```

## 30-second tour

<!-- name: test_index_quick_tour -->
```python
from tagz import Page, html

page = Page(
    lang="en",
    body_element=html.body(
        html.h1("Hello"),
        html.p("from ", html.strong("tagz")),
    ),
    head_elements=(
        html.meta(charset="utf-8"),
        html.title("tagz"),
    ),
)

output = page.to_html5(pretty=True)
assert "<!doctype html>" in output
assert "<strong>tagz</strong>" in output.replace("\n", "").replace("\t", "")
```

## Pick the doc that fits your need

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} 📘 Tutorials
:link: tutorials/index
:link-type: doc

Learning-oriented. Step-by-step lessons that take you from zero to
working code. Start here if you're new.
:::

:::{grid-item-card} 🛠 How-to guides
:link: how-to/index
:link-type: doc

Task-oriented. Self-contained recipes that solve a single problem —
streaming, parsing, escaping, embedding binary data, and more.
:::

:::{grid-item-card} 📖 Reference
:link: reference/index
:link-type: doc

Information-oriented. The exhaustive API surface: every class, every
method, every option, with type signatures.
:::

:::{grid-item-card} 💡 Explanation
:link: explanation/index
:link-type: doc

Understanding-oriented. The "why" — design decisions, the escaping
model, callables and laziness, and the `tagz.aio` streaming model.
:::

::::

## Install

```bash
pip install tagz
# or with uv:
uv add tagz
```

Requires Python 3.10+. See [Installation](reference/installation.md) for
project-integration notes.

## Project links

- **Source:** <https://github.com/mosquito/tagz>
- **Issues:** <https://github.com/mosquito/tagz/issues>
- **PyPI:** <https://pypi.org/project/tagz/>
