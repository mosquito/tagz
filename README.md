[![tests](https://github.com/mosquito/tagz/actions/workflows/tests.yml/badge.svg)](https://github.com/mosquito/tagz/actions/workflows/tests.yml)
[![Coveralls](https://coveralls.io/repos/github/mosquito/tagz/badge.svg?branch=master)](https://coveralls.io/github/mosquito/tagz?branch=master)
[![Latest Version](https://img.shields.io/pypi/v/tagz.svg)](https://pypi.python.org/pypi/tagz/)
[![python wheel](https://img.shields.io/pypi/wheel/tagz.svg)](https://pypi.python.org/pypi/tagz/)
[![Python Versions](https://img.shields.io/pypi/pyversions/tagz.svg)](https://pypi.python.org/pypi/tagz/)
[![license](https://img.shields.io/pypi/l/tagz.svg)](https://pypi.python.org/pypi/tagz/)

# `tagz`

`tagz` – is an extremely simple library for building html documents without using templates, 
just with python code.

<!-- name: test_page_render -->
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
from tagz import html

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
assert str(tag) == '<div foo="bar"></div>', str(tag)
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

<!-- name: test_pretty_printing -->
```python
from tagz import html

result = html.div(
    "Hello", html.strong("world"),
).to_string(pretty=True)

assert result == "<div>\n\tHello\n\t<strong>\n\t\tworld\n\t</strong>\n</div>\n"
```

## Iterating string generation

For memory-efficient or streaming scenarios, `tagz` provides three methods for incremental HTML generation:

### `iter_lines()` - Line-by-line iteration (recommended)

The `iter_lines()` method yields complete lines of pretty-printed HTML, making it ideal for streaming to files or network sockets:

<!-- name: test_iter_lines_basic -->
```python
from tagz import html

tag = html.div(
    html.p("First paragraph"),
    html.p("Second paragraph"),
)

# Iterate line by line (always pretty-printed)
lines = list(tag.iter_lines())
assert lines == [
    "<div>",
    "\t<p>",
    "\t\tFirst paragraph",
    "\t</p>",
    "\t<p>",
    "\t\tSecond paragraph",
    "\t</p>",
    "</div>",
]
```

You can customize the indentation character:

<!-- name: test_iter_lines_indent -->
```python
from tagz import html

tag = html.div(html.p("Hello"))

# Customize indentation (default is tab)
lines = list(tag.iter_lines(indent_char="  "))
assert lines == [
    "<div>",
    "  <p>",
    "    Hello",
    "  </p>",
    "</div>",
]
```

Stream to a file:

<!-- name: test_iter_lines_file -->
```python
from tagz import html
from tempfile import NamedTemporaryFile

tag = html.div(html.p("Content"))

# Stream to a file
with NamedTemporaryFile(mode="w", suffix=".html", delete=True) as f:
    for line in tag.iter_lines():
        f.write(line + "\n")
    f.flush()
```

### `iter_chunk()` - Fixed-size chunk iteration

The `iter_chunk()` method yields HTML in fixed-size chunks, perfect for network transmission or buffered I/O:

<!-- name: test_iter_chunk_basic -->
```python
from tagz import html

tag = html.div(
    html.p("First paragraph with some content"),
    html.p("Second paragraph with more content"),
)

# Generate HTML in 50-byte chunks
chunks = list(tag.iter_chunk(chunk_size=50))

# Each chunk is approximately 50 bytes (except possibly the last one)
assert all(len(chunk) <= 50 or chunk == chunks[-1] for chunk in chunks)

# Verify reconstruction
assert "".join(chunks) == tag.to_string()
```

You can use it with pretty printing and custom indentation:

<!-- name: test_iter_chunk_pretty -->
```python
from tagz import html
from functools import partial

content = "Paragraph {}"
# Create a large tag with many lazy evaluated children
tag = html.div(*[html.p(partial(content.format, i)) for i in range(1000)])

# Pretty-printed chunks with custom indent
chunks = list(tag.iter_chunk(chunk_size=1024, pretty=True, indent_char="  "))

# Verify reconstruction works correctly
assert "".join(chunks) == tag.to_string(pretty=True).replace("\t", "  ")
```

### `iter_string()` - Fragment-by-fragment iteration

The `iter_string()` method yields tiny fragments of HTML as they are generated, useful for very fine-grained control:

<!-- name: test_iter_string -->
```python
from tagz import html

tag = html.div(html.p("Hello"))

# Generate HTML in small fragments (non-pretty)
result = "".join(tag.iter_string())
assert result == "<div><p>Hello</p></div>"

# Also works with pretty printing
pretty_result = "".join(tag.iter_string(pretty=True))
assert pretty_result == "<div>\n\t<p>\n\t\tHello\n\t</p>\n</div>\n"
```

All these methods are useful when generating large HTML documents where you want to stream the output without building the entire string in memory.

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

## Controlling Attribute Absence

You can use the special value `ABSENT` to dynamically remove an attribute from a tag. This is useful for callables that may want to omit an attribute based on logic.

<!-- name: test_absent_attr -->
```python
from tagz import html, ABSENT

present = True

def attr():
     return "value" if present else ABSENT

tag = html.div(test=attr)
assert str(tag) == '<div test="value"></div>'

present = False
assert str(tag) == "<div></div>"
```

## Raw Content in Script and Style

Content inside `<script>` and `<style>` tags is not escaped by default. This allows you to embed raw JS/CSS.

<!-- name: test_raw_script_style -->
```python
from tagz import html

style = html.style("body {margin: 0; padding: 0;}")
assert str(style) == "<style>body {margin: 0; padding: 0;}</style>"

script = html.script('''console.log(1 > 2 && 3 < 2 && "0" === '0');''')
assert str(script) == '''<script>console.log(1 > 2 && 3 < 2 && "0" === '0');</script>'''
```

## Raw HTML Content

Use the `Raw` class to embed completely unescaped HTML content. This is useful when you have pre-rendered HTML fragments or need to bypass all escaping:

<!-- name: test_raw_html -->
```python
from tagz import html, Raw

# Create raw HTML content (not escaped, no wrapper tags)
raw = Raw("<div>raw content & more</div>")
assert str(raw) == "<div>raw content & more</div>"

# Can be used as a child of other tags
container = html.div(raw)
assert str(container) == "<div><div>raw content & more</div></div>"

# Raw content is never indented in pretty mode
assert raw.to_string(pretty=True) == "<div>raw content & more</div>"
```

**Warning:** `Raw` is completely unescaped and unsafe against XSS attacks. Only use it with trusted content or when you have already sanitized the HTML.

## Tag classes API

The `classes` property supports assignment via set, list, tuple, or space-separated string, and raises a `TypeError` for invalid types.

<!-- name: test_classes_setter -->
```python
from tagz import html

tag = html.div()
tag.classes = "foo bar"
assert tag.classes == {"foo", "bar"}
tag.classes = ["baz"]
assert tag.classes == {"baz"}
```

You can use either `class` or `classes` as a keyword argument or attribute key. Both will be mapped to the HTML `class` attribute and the internal `classes` set. This allows for more natural Python code:

<!-- name: test_class_attribute -->
```python
from tagz import html

tag = html.div(classes=["foo", "bar"])
# Classes are stored as a set internally
assert str(tag) == '<div class="bar foo"></div>', str(tag)

tag["class"] = "baz"
assert str(tag) == '<div class="baz"></div>', str(tag)

tag["classes"] = "spam eggs"
# Classes was splitted and are stored as a set internally
assert str(tag) == '<div class="eggs spam"></div>', str(tag)
```

## Escaping Callable Children

If a callable child returns a string, it will be escaped by default (unless the tag disables escaping, e.g., `<script>` or `<style>`):

<!-- name: test_escaped_callable_child -->
```python
from tagz import html

def child():
    return "<script>alert('xss');</script>"

tag = html.div(child)
assert str(tag) == "<div>&lt;script&gt;alert(&#x27;xss&#x27;);&lt;/script&gt;</div>"
```

## Boolean Attribute Handling

Setting an attribute to `True` renders it as a boolean attribute (e.g., `<input checked>`). Setting it to `False` removes the attribute:

<!-- name: test_boolean_attribute -->
```python
from tagz import html

tag = html.input(type="checkbox", checked=True)
assert str(tag) == '<input checked type="checkbox"/>'
tag["checked"] = False
assert str(tag) == '<input type="checkbox"/>'
```

## Data URI helpers

You can embed binary data directly in HTML attributes using `data_uri` and `open_data_uri`:

<!-- name: test_data_uri -->
```python
from tagz import data_uri

src = data_uri(b"hello world", media_type="text/plain")
assert src == "data:text/plain;base64,aGVsbG8gd29ybGQ="
```

Or use `open_data_uri` to read and encode a file directly:

<!-- name: test_open_data_uri -->
```python
from tempfile import NamedTemporaryFile
from tagz import open_data_uri, html

with NamedTemporaryFile("wb", suffix=".png") as f:
    # Write a minimal PNG file
    f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
            b"\x89\x00\x00\x00\nIDATx\xdac\xf8\x0f\x00\x01\x01"
            b"\x01\x00\x18\xdd\x03\xe2\x00\x00\x00\x00IEND\xaeB`\x82")
    f.flush()
    f.seek(0)

    src = open_data_uri(f.name, media_type="image/png")
    img_tag = html.img(src=src, alt="Nothing")
    assert str(img_tag).startswith(
        '<img alt="Nothing" src="data:image/png;base64,'
        'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcS'
        'JAAAACklEQVR42mP4DwABAQEAGN0D4gAAAABJRU5ErkJggg=='
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
