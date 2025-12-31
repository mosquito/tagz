from copy import copy

import pytest

from tagz import HTML, Page, Style, StyleSheet, Tag, html, ABSENT, Raw


@pytest.fixture
def sample_html_page():
    # Create a sample HTML page for testing
    return Page(
        lang="en",
        body_element=html.body(
            html.h1("Hello, World!"),
            html.p("This is a test."),
        ),
        head_elements=[
            html.title("Sample Page"),
        ],
    )


def test_tag_creation(subtests):
    with subtests.test("Creating Tag via Tag class"):
        tag = Tag("div", classes=["container"], id="main")
        assert "container" in tag.classes
        assert tag.name == "div"
        assert tag["id"] == "main"

    with subtests.test("Creating Tag via html factory"):
        tag = html.div(classes=["container"], id="main")
        assert "container" in tag.classes
        assert tag.name == "div"
        assert tag["id"] == "main"


def test_tag_classes_manipulation(subtests):
    with subtests.test("classes on init"):
        tag = html.div(classes=["new-class"])
        assert tag.classes == {"new-class"}

    with subtests.test("manipulating classes set"):
        tag.classes.add("new-class")
        assert tag.classes == {"new-class"}

    with subtests.test("removing classes from set"):
        tag.classes.remove("new-class")
        assert "new-class" not in tag.classes

    with subtests.test("setting classes attribute"):
        tag.classes = {"class1", "class2"}
        assert tag.classes == {"class1", "class2"}

    with subtests.test("setting classes to different types"):
        tag.classes = []
        assert tag.classes == set()

    with subtests.test("setting classes to strings with spaces"):
        tag.classes = "class3 class4"
        assert tag.classes == {"class3", "class4"}

    with subtests.test("setting classes to invalid type raises TypeError"):
        with pytest.raises(TypeError):
            tag.classes = 123  # Invalid type


def test_tag_string_representation():
    tag = html.p("Hello, World!", html.a("go to index", "", href="/"), html.i())
    assert str(tag) == '<p>Hello, World!<a href="/">go to index</a><i></i></p>'
    assert tag.to_string(pretty=True) == (
        '<p>\n\tHello, World!\n\t<a href="/">\n\t\tgo to index\n\t</a>\n\t<i>\n\t</i>\n</p>\n'
    )
    assert html.my_custom_tag is html.my_custom_tag
    assert str(html.my_custom_tag()) == "<my-custom-tag></my-custom-tag>"
    assert str(html.my_custom_tag("test")) == "<my-custom-tag>test</my-custom-tag>"


def test_pretty_deep_nesting():
    deep_tag = html.div(
        html.section(
            html.span(
                html.article(
                    html.p(
                        "Deeply nested paragraph.",
                        html.span("With a span inside."),
                    )
                )
            )
        )
    )

    expected_pretty = (
        "<div>\n"
        "\t<section>\n"
        "\t\t<span>\n"
        "\t\t\t<article>\n"
        "\t\t\t\t<p>\n"
        "\t\t\t\t\tDeeply nested paragraph.\n"
        "\t\t\t\t\t<span>\n"
        "\t\t\t\t\t\tWith a span inside.\n"
        "\t\t\t\t\t</span>\n"
        "\t\t\t\t</p>\n"
        "\t\t\t</article>\n"
        "\t\t</span>\n"
        "\t</section>\n"
        "</div>\n"
    )

    assert deep_tag.to_string(pretty=True) == expected_pretty


def test_html_generation(sample_html_page):
    html_str = sample_html_page.to_html5()
    assert "<!doctype html>" in html_str
    assert '<html lang="en">' in html_str
    assert "<head>" in html_str
    assert "<title>Sample Page</title>" in html_str
    assert "<body>" in html_str
    assert "<h1>Hello, World!</h1>" in html_str
    assert "<p>This is a test.</p>" in html_str


def test_html_class_factory():
    html_class = HTML({"custom-tag": {"__default_children__": ("Hello",)}})
    custom_tag = html_class.custom_tag()
    assert isinstance(custom_tag, Tag)
    assert str(custom_tag) == "<custom-tag>Hello</custom-tag>"


def test_tag_attributes(subtests):
    with subtests.test("Setting attributes via constructor"):
        tag = html.div(id="main", classes=["container", "fluid"], data_role="page")
        assert tag["id"] == "main"
        assert "container" in tag.classes
        assert "fluid" in tag.classes
        assert tag["data-role"] == "page"
        assert (
            str(tag) == '<div class="container fluid" data-role="page" id="main"></div>'
        )

    with subtests.test("Setting attributes via item assignment"):
        tag = html.div()
        tag["id"] = "main"
        tag["classes"] = ["container", "fluid"]
        tag["data-role"] = "page"
        assert tag["id"] == "main"
        assert "container" in tag.classes
        assert "fluid" in tag.classes
        assert tag["data-role"] == "page"
        assert (
            str(tag) == '<div class="container fluid" data-role="page" id="main"></div>'
        )

    with subtests.test("Setting attribute to None renders as boolean attribute"):
        tag = html.input(type="checkbox", checked=None)
        assert str(tag) == '<input checked type="checkbox"/>'

    with subtests.test("Setting attribute to False removes it"):
        tag = html.input(type="checkbox", checked=False)
        assert str(tag) == '<input type="checkbox"/>'

    with subtests.test("Setting attribute to True renders as boolean attribute"):
        tag = html.input(type="checkbox", disabled=True)
        assert str(tag) == '<input disabled type="checkbox"/>'

    with subtests.test("Attribute value escaping"):
        tag = html.div(title='This is a "quote" & test')
        expected = '<div title="This is a &quot;quote&quot; &amp; test"></div>'
        assert str(tag) == expected

    with subtests.test("deleting attributes"):
        tag = html.div(id="to-delete", classes=["temp"])
        del tag["id"]
        assert "id" not in tag.attributes
        assert str(tag) == '<div class="temp"></div>'

    with subtests.test("attribute absent"):
        tag = html.div(test="value")
        assert tag["test"] == "value"

        tag["test"] = ABSENT
        assert "test" not in tag.attributes
        assert str(tag) == "<div></div>"


def test_unescaped_attribute(subtests):
    with subtests.test("Integer attribute value"):
        tag = html.div(foo=123)
        assert str(tag) == '<div foo="123"></div>'
    with subtests.test("None attribute value"):
        tag = html.div(foo=None)
        assert str(tag) == "<div foo></div>"
    with subtests.test("True attribute value"):
        tag = html.div(foo=True)
        assert str(tag) == "<div foo></div>"
    with subtests.test("Unsafe attribute value"):
        tag = html.div(foo="<b>unsafe</b>")
        # All attribute values must be escaped
        assert str(tag) == '<div foo="&lt;b&gt;unsafe&lt;/b&gt;"></div>'


def test_tag_features():
    div = html.div()

    assert str(div) == "<div></div>"
    div.append(html.strong("hello"))

    assert str(div) == "<div><strong>hello</strong></div>"
    div["id"] = "foo"

    assert div["id"] == "foo"
    div["custom_attr"] = " custom value "

    div = html.div()
    div["custom"] = None
    assert str(div) == "<div custom></div>"

    div = html.div(classes=["foo", "bar"])
    assert str(div) == '<div class="bar foo"></div>'

    div = html.div()
    assert repr(div) == "<div></div>"

    div = html.div("Hello")
    assert repr(div) == "<div>...</div>"


def test_style():
    assert (
        str(Style(text_align="center", padding=0)) == "padding: 0; text-align: center;"
    )

    style = Style()
    assert str(style) == ""

    style["padding"] = 0
    assert str(style) == "padding: 0;"

    style["margin"] = 0
    assert str(style) == "margin: 0; padding: 0;"

    assert str(
        html.div("red", style=Style(color="#ff0000")),
    ) == ('<div style="color: #ff0000;">red</div>')


def test_stylesheet():
    style_sheet = StyleSheet()
    style_sheet["body"] = Style(background_color="#000000", color="#ffffff")
    style_sheet[("div", "a", "table")] = Style(
        background_color="#111111", color="#cccccc"
    )

    assert str(style_sheet) == (
        "body {background-color: #000000; color: #ffffff;}\n"
        "div, a, table {background-color: #111111; color: #cccccc;}"
    )


def test_tag_copy():
    tag = html.div(name="foo")
    clone = copy(tag)
    clone["name"] = "bar"

    assert tag != clone
    assert tag["name"] != clone["name"]
    assert tag["name"] == "foo"
    assert clone["name"] == "bar"


def test_void_tags():
    br = html.br()
    assert str(br) == "<br/>"
    assert repr(br) == "<br/>"

    img = html.img(src="image.png", alt="An image")
    assert str(img) == '<img alt="An image" src="image.png"/>'
    assert repr(img) == '<img alt="An image" src="image.png"/>'

    with pytest.raises(ValueError):
        html.img("This should not be allowed in a void tag")

    tag = html.br()
    with pytest.raises(ValueError):
        tag.append(html.span("Not allowed"))


def test_stylesheets():
    style = StyleSheet(
        {
            "body": Style(margin="0", padding="0"),
            (".container", ".container-fluid"): Style(
                transition="opacity 600ms ease-in"
            ),
        }
    )
    assert str(style) == (
        "body {margin: 0; padding: 0;}\n"
        ".container, .container-fluid {transition: opacity 600ms ease-in;}"
    )


def test_style_unescaped():
    style = html.style("body {margin: 0; padding: 0;}")
    assert str(style) == "<style>body {margin: 0; padding: 0;}</style>"

    style = html.style("body > div {color: red;}")
    assert str(style) == "<style>body > div {color: red;}</style>"


def test_script_unescaped():
    script = html.script("""console.log(1 > 2 && 3 < 2 && "0" === '0');""")
    assert (
        str(script)
        == """<script>console.log(1 > 2 && 3 < 2 && "0" === '0');</script>"""
    )


def test_pre_escaped_content():
    div = html.pre("""console.log(1 > 2 && 3 < 2 && "0" === '0');""")
    assert (
        str(div)
        == "<pre>console.log(1 &gt; 2 &amp;&amp; 3 &lt; 2 &amp;&amp; &quot;0&quot; === &#x27;0&#x27;);</pre>"
    )


TEST_PAGE = """
<!doctype html>
<html lang="en">
\t<head>
\t\t<meta charset="utf-8"/>
\t\t<meta content="width=device-width, initial-scale=1" name="viewport"/>
\t\t<title>
\t\t\ttagz example page
\t\t</title>
\t\t<link href="/static/css/bootstrap.min.css" rel="stylesheet"/>
\t\t<script src="/static/js/bootstrap.bundle.min.js">
\t\t</script>
\t\t<style>
\t\t\tbody {margin: 0; padding: 0;}
\t\t\t.container, .container-fluid {transition: opacity 600ms ease-in;}
\t\t</style>
\t</head>
\t<body>
\t\t<h1>
\t\t\tHello
\t\t</h1>
\t\t<div>
\t\t\t<strong>
\t\t\t\tworld
\t\t\t</strong>
\t\t</div>
\t\t<a href="https://example.com/">
\t\t\texample link
\t\t\t<i>
\t\t\t\twith italic text
\t\t\t</i>
\t\t</a>
\t</body>
</html>
"""


def test_webpage():
    page = Page(
        lang="en",
        body_element=html.body(
            html.h1("Hello"),
            html.div(
                html.strong("world"),
            ),
            html.a(
                "example link", html.i("with italic text"), href="https://example.com/"
            ),
        ),
        head_elements=(
            html.meta(charset="utf-8"),
            html.meta(name="viewport", content="width=device-width, initial-scale=1"),
            html.title("tagz example page"),
            html.link(href="/static/css/bootstrap.min.css", rel="stylesheet"),
            html.script(src="/static/js/bootstrap.bundle.min.js"),
            html.style(
                StyleSheet(
                    {
                        "body": Style(padding="0", margin="0"),
                        (".container", ".container-fluid"): Style(
                            transition="opacity 600ms ease-in"
                        ),
                    }
                )
            ),
        ),
    )

    assert page.to_html5(True).strip() == TEST_PAGE.strip()

def test_raw():
    raw = Raw("<div>raw content & more</div>")
    assert str(raw) == "<div>raw content & more</div>"

    container = html.div(raw)
    assert str(container) == "<div><div>raw content & more</div></div>"

    assert raw.to_string(pretty=True) == "<div>raw content & more</div>"


def test_iter_lines():
    # Test basic iteration
    tag = html.div(
        html.p("Hello"),
        html.p("World"),
    )

    lines = list(tag.iter_lines())
    expected_lines = [
        "<div>",
        "\t<p>",
        "\t\tHello",
        "\t</p>",
        "\t<p>",
        "\t\tWorld",
        "\t</p>",
        "</div>",
    ]
    assert lines == expected_lines

    # Test with custom indent character
    lines_spaces = list(tag.iter_lines(indent_char="  "))
    expected_spaces = [
        "<div>",
        "  <p>",
        "    Hello",
        "  </p>",
        "  <p>",
        "    World",
        "  </p>",
        "</div>",
    ]
    assert lines_spaces == expected_spaces

    # Test that joining lines with newlines gives same result as to_string(pretty=True)
    assert "\n".join(tag.iter_lines()) + "\n" == tag.to_string(pretty=True)

    # Test with nested tags
    nested = html.div(
        html.section(
            html.p("Nested content"),
        ),
    )
    nested_lines = list(nested.iter_lines())
    assert nested_lines == [
        "<div>",
        "\t<section>",
        "\t\t<p>",
        "\t\t\tNested content",
        "\t\t</p>",
        "\t</section>",
        "</div>",
    ]

    # Test with void elements
    void_tag = html.div(html.br(), "text", html.hr())
    void_lines = list(void_tag.iter_lines())
    assert void_lines == [
        "<div>",
        "\t<br/>",
        "\ttext",
        "\t<hr/>",
        "</div>",
    ]

    # Test with multi-line string content (like StyleSheet)
    style_content = "body {margin: 0;}\n.container {padding: 10px;}"
    style_tag = html.style(style_content)
    style_lines = list(style_tag.iter_lines())
    assert style_lines == [
        "<style>",
        "\tbody {margin: 0;}",
        "\t.container {padding: 10px;}",
        "</style>",
    ]

    # Test empty tag
    empty = html.div()
    empty_lines = list(empty.iter_lines())
    assert empty_lines == ["<div>", "</div>"]

    # Test single text content
    simple = html.p("Simple text")
    simple_lines = list(simple.iter_lines())
    assert simple_lines == [
        "<p>",
        "\tSimple text",
        "</p>",
    ]