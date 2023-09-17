`tagz`
======

[![Github Actions](https://github.com/mosquito/tagz/workflows/tests/badge.svg)](https://github.
com/mosquito/tagz/actions?query=branch%3Amaster)
[![Coveralls](https://coveralls.io/repos/github/mosquito/tagz/badge.svg?branch=master)](https://coveralls.
io/github/mosquito/tagz?branch=master)
[![Latest Version](https://img.shields.io/pypi/v/tagz.svg)](https://pypi.python.org/pypi/tagz/)
[![python wheel](https://img.shields.io/pypi/wheel/tagz.svg)](https://pypi.python.org/pypi/tagz/)
[![Python Versions](https://img.shields.io/pypi/pyversions/tagz.svg)](https://pypi.python.org/pypi/tagz/)
[![license](https://img.shields.io/pypi/l/tagz.svg)](https://pypi.python.org/pypi/tagz/)


`tagz` is an extremely simple library for building html documents without using templates, 
just with python code.

```python
from tagz import html, Page


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
        html.link(href="/static/css/bootstrap.min.css"),
        html.script(src="/static/js/bootstrap.bundle.min.js"),
        html.style(
            ".container, .container-fluid {transition:opacity 600ms ease-in;}"
        )
    ),
)

# `pretty=False` should be faster but performs not a human-readable result
print(page.to_html5(pretty=True))
```

writes something like this:

```html
<!doctype html>
<html lang="en">
	<head>
		<meta charset="utf-8"/>
		<meta name="viewport" content="width=device-width, initial-scale=1"/>
		<title>
			tagz example page
		</title>
		<link href="/static/css/bootstrap.min.css"/>
		<script src="/static/js/bootstrap.bundle.min.js">
		</script>
		<style>
			.container, .container-fluid {transition:opacity 600ms ease-in;}
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

