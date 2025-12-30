[![tests](https://github.com/mosquito/tagz/actions/workflows/tests.yml/badge.svg)](https://github.com/mosquito/tagz/actions/workflows/tests.yml)
[![Coveralls](https://coveralls.io/repos/github/mosquito/tagz/badge.svg?branch=master)](https://coveralls.io/github/mosquito/tagz?branch=master)
[![Latest Version](https://img.shields.io/pypi/v/tagz.svg)](https://pypi.python.org/pypi/tagz/)
[![python wheel](https://img.shields.io/pypi/wheel/tagz.svg)](https://pypi.python.org/pypi/tagz/)
[![Python Versions](https://img.shields.io/pypi/pyversions/tagz.svg)](https://pypi.python.org/pypi/tagz/)
[![license](https://img.shields.io/pypi/l/tagz.svg)](https://pypi.python.org/pypi/tagz/)

# `tagz`

`tagz` – is an extremely simple library for building html documents without using templates, 
just with python code.

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
		<link href="/static/css/bootstrap.min.css" rel="stylesheet"/>
		<script src="/static/js/bootstrap.bundle.min.js">
		</script>
		<style>
			body {padding: 0; margin: 0;}
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

# Features

`tagz` provides the following features:

## Callable children and attributes

You can pass a function (callable) as a child or as an attribute value to any tag. This allows for lazy or dynamic content generation.

### Callable children

<!-- name: test_callable_child -->
```python
from tagz import html

def child():
    return "hello"

tag = html.div(child)
assert str(tag) == "<div>hello</div>"
```

Or return another tag:

<!-- name: test_callable_child -->
```python
# Callable child returning a tag
def child_tag():
    return html.span("world")

tag = html.div(child_tag)
assert str(tag) == "<div><span>world</span></div>"
```

You can also use `append` with callables:

<!-- name: test_callable_append -->
```python
from tagz import html

tag = html.div()
tag.append(lambda: "foo")
assert str(tag) == "<div>foo</div>"
```

### Callable attribute values

You can use callables as attribute values. If the result is a not an string, it will be converted to string and escaped as an attribute value.

<!-- name: test_callable_attrs -->
```python
from tagz import html

def attr():
    return "bar"

tag = html.div(foo=attr)
assert str(tag) == '<div foo="bar"/>', str(tag)
```

## Custom tags is supported

Add custom tags by using underscore `_` in the name:

<!-- name: test_custom_tag -->
```python
from tagz import html
assert str(html.my_custom_tag("hello")) == "<my-custom-tag>hello</my-custom-tag>" 
```

## Pretty printing html

You can pretty print the html output with `to_string(pretty=True)` or `to_html5(pretty=True)` methods:

```python
from tagz import html

print(
    html.div(
        "Hello", html.strong("world"),
    ).to_string(pretty=True)
)
#<div>
#	Hello
#	<strong>
#		world
#	</strong>
#</div>
```

## `Style` and `StyleSheet` helper objects

`Style` helper object encapsulating css styles:

<!-- name: test_custom_tag -->
```python
from tagz import Style
assert str(Style(color="#ffffff")) == "color: #ffffff;"
```


`StyleSheet` helper object encapsulating css stylesheet:

<!-- name: test_stylesheet -->
```python
from tagz import Style, StyleSheet

# body {padding: 0;margin: 0}
# a, div {transition: opacity 600ms ease-in}
print(
    str(
        StyleSheet({
            "body": Style(padding="0", margin="0"),
            ("div", "a"): Style(transition="opacity 600ms ease-in"),
        })
    )
)
```

# More examples

## Building page from parts

You can reuse the code, and assemble the page piece by piece, 
to do this you can modify elements already added to the tags:

```python
from tagz import html, Page

# Make an content element
content = html.div(id='content')

page = Page(
    lang="en",
    body_element=html.body(
        html.h1("Example page"),
        html.hr(),
        # Adding it to the page
        content,
    ),
    head_elements=(
        html.meta(charset="utf-8"),
        html.title("tagz partial page"),
    ),
)

content.append("Example page content")

print(page.to_html5(pretty=True))
```

This prints something like this:  

```html
<!doctype html>
<html lang="en">
	<head>
		<meta charset="utf-8"/>
		<title>
			tagz example page
		</title>
	</head>
	<body>
		<h1>
			Example page
		</h1>
		<hr/>
		<div id="content">
			Example page content
		</div>
	</body>
</html>
```

## Convert CSV to html table

```python
from io import StringIO
from urllib.request import urlopen
from csv import reader
from tagz import html, Page, Style

url = (
    'https://media.githubusercontent.com/media/datablist/'
    'sample-csv-files/main/files/organizations/'
    'organizations-10000.csv'
)

csv = reader(StringIO(urlopen(url).read().decode()))
table = html.table(border='1', style=Style(border_collapse="collapse"))
content = list(csv)

# Make table header 
table.append(html.tr(*map(html.th, content[0])))

# Add table rows
for csv_row in content[1:]:
    table.append(html.tr(*map(html.td, csv_row)))

page = Page(
    lang="en",
    body_element=html.body(
        html.h1("Converted CSV"),
        table,
        "Content of this page has been automatically converted from",
        html.a(url, href=url),
    ),
    head_elements=(
        html.meta(charset="utf-8"),
        html.title("tagz csv example page"),
    ),
)

with open("/tmp/csv.html", "w") as fp:
    fp.write(page.to_html5())
```