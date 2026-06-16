<p align="center">
  <img src="https://raw.githubusercontent.com/mosquito/tagz/master/docs/_static/logo.svg" alt="tagz" width="312">
</p>

[![tests](https://github.com/mosquito/tagz/actions/workflows/tests.yml/badge.svg)](https://github.com/mosquito/tagz/actions/workflows/tests.yml)
[![Coveralls](https://coveralls.io/repos/github/mosquito/tagz/badge.svg?branch=master)](https://coveralls.io/github/mosquito/tagz?branch=master)
[![Latest Version](https://img.shields.io/pypi/v/tagz.svg)](https://pypi.python.org/pypi/tagz/)
[![python wheel](https://img.shields.io/pypi/wheel/tagz.svg)](https://pypi.python.org/pypi/tagz/)
[![Python Versions](https://img.shields.io/pypi/pyversions/tagz)](https://pypi.org/project/tagz/)
[![license](https://img.shields.io/pypi/l/tagz.svg)](https://pypi.python.org/pypi/tagz/)

# `tagz`

A lightweight, type-safe Python library for building and parsing HTML documents programmatically without templates.

> 📚 **Full documentation:** <https://mosquito.github.io/tagz/>

## Overview

`tagz` lets you construct HTML using pure Python code with a clean, intuitive API. No template engines, no DSLs — just Python functions and objects that map directly to HTML elements.

**Key Features:**

- **Programmatic HTML construction** — build documents using Python objects and methods
- **HTML parser** — parse existing HTML strings back into manipulable `Tag` objects
- **Type-safe** — full mypy support with comprehensive type annotations
- **Streaming support** — memory-efficient rendering with `iter_lines()`, `iter_chunk()`, and `iter_string()`
- **Automatic escaping** — XSS protection enabled by default
- **CSS helpers** — built-in `Style` and `StyleSheet` objects
- **Fragments and raw** — group elements without wrapper tags, or splice in pre-rendered HTML
- **Page objects** — high-level API for complete HTML documents with DOCTYPE support

## Installation

```bash
pip install tagz
```

or with [uv](https://docs.astral.sh/uv/):

```bash
uv add tagz
```

Requires Python 3.10+.

## Quick start

<!-- name: test_readme_quick_start -->
```python
from tagz import Page, StyleSheet, Style, html


page = Page(
    lang="en",
    body_element=html.body(
        html.h1("Hello"),
        html.div(
            html.strong("world"),
        ),
        html.a(
            "example link",
            html.i("with italic text"),
            href="https://example.com/"
        ),
    ),
    head_elements=(
        html.meta(charset="utf-8"),
        html.meta(name="viewport", content="width=device-width, initial-scale=1"),
        html.title("tagz example page"),
        html.link(href="/static/css/bootstrap.min.css", rel="stylesheet"),
        html.script(src="/static/js/bootstrap.bundle.min.js"),
        html.style(
            StyleSheet({
                "body": Style(padding="0", margin="0"),
                (".container", ".container-fluid"): Style(transition="opacity 600ms ease-in"),
            })
        )
    ),
)

# `pretty=False` is the fast path; pretty=True produces human-readable output.
output = page.to_html5(pretty=True)
assert output.startswith("<!doctype html>")
assert "<strong>" in output
```

The pretty-printed output looks like:

```html
<!doctype html>
<html lang="en">
	<head>
		<meta charset="utf-8"/>
		<meta content="width=device-width, initial-scale=1" name="viewport"/>
		<title>
			tagz example page
		</title>
		<link href="/static/css/bootstrap.min.css" rel="stylesheet"/>
		<script src="/static/js/bootstrap.bundle.min.js">
		</script>
		<style>
			body {margin: 0; padding: 0;}
			.container, .container-fluid {transition: opacity 600ms ease-in;}
		</style>
	</head>
	<body>
		<h1>
			Hello
		</h1>
		<div>
			<strong>
				world
			</strong>
		</div>
		<a href="https://example.com/">
			example link
			<i>
				with italic text
			</i>
		</a>
	</body>
</html>
```

## Where to next?

The full documentation is organised in the [Diátaxis](https://diataxis.fr/) style:

- **[Tutorials](https://mosquito.github.io/tagz/tutorials/)** — guided lessons that take you from zero to a working page, parser, or streamed document.
- **[How-to guides](https://mosquito.github.io/tagz/how-to/)** — recipe-style answers to specific problems (streaming, callables, async data, `data:` URIs, CSV → table, …).
- **[Reference](https://mosquito.github.io/tagz/reference/)** — the full API surface with type signatures.
- **[Explanation](https://mosquito.github.io/tagz/explanation/)** — design rationale: escaping model, callables and laziness, why there's no async render path.

## Feature highlights

| Feature | Read more |
| ------- | --------- |
| Callable children & attributes | [How-to: lazy children](https://mosquito.github.io/tagz/how-to/lazy-children-with-callables.html) |
| Conditional attributes via `ABSENT` | [How-to: conditional attributes](https://mosquito.github.io/tagz/how-to/conditional-attributes-with-absent.html) |
| Boolean attributes (`checked`, `disabled`, …) | [How-to: boolean attributes](https://mosquito.github.io/tagz/how-to/boolean-attributes.html) |
| Custom / non-standard tag names | [How-to: custom tags](https://mosquito.github.io/tagz/how-to/custom-tags.html) |
| Fragments and unescaped `Raw` content | [How-to: fragments vs raw](https://mosquito.github.io/tagz/how-to/fragments-vs-raw.html) |
| Inline `style=` and `<style>` blocks | [How-to: inline & embedded CSS](https://mosquito.github.io/tagz/how-to/inline-and-embedded-css.html) |
| Streaming to file / socket / ASGI | [How-to: stream to a socket](https://mosquito.github.io/tagz/how-to/stream-to-socket.html) |
| `data:` URIs for inline binary data | [How-to: embed binary data](https://mosquito.github.io/tagz/how-to/embed-binary-with-data-uri.html) |
| Pre-resolving async data | [How-to: prefetch async data](https://mosquito.github.io/tagz/how-to/prefetch-async-data.html) |
| Serving HTML fragments to htmx (aiohttp) | [How-to: htmx + aiohttp](https://mosquito.github.io/tagz/how-to/htmx-with-aiohttp.html) — full demo in [`examples/htmx-asyncio`](examples/htmx-asyncio/) |
| Parsing existing HTML | [Tutorial: parse and modify](https://mosquito.github.io/tagz/tutorials/parsing-and-modifying.html) |

## License

MIT — see [LICENSE](LICENSE).
