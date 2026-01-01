from copy import copy

import pytest

from tagz import (
    HTML,
    Page,
    Style,
    StyleSheet,
    Tag,
    html,
    ABSENT,
    Raw,
    Fragment,
    parse,
    TagParser,
)


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

    # Test Style with dict arg (covers args parameter)
    style_dict = Style({"color": "red"})
    assert "color: red;" in str(style_dict)

    # Test with underscored kwargs
    style_underscored = Style(font_size="12px", background_color="blue")
    assert "font-size: 12px;" in str(style_underscored)
    assert "background-color: blue;" in str(style_underscored)

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


def test_fragment(subtests):
    with subtests.test("basic fragment with multiple children"):
        fragment = Fragment(
            html.h1("Title"),
            html.p("Paragraph 1"),
            html.p("Paragraph 2"),
        )
        expected = "<h1>Title</h1><p>Paragraph 1</p><p>Paragraph 2</p>"
        assert str(fragment) == expected

    with subtests.test("fragment as child of another tag"):
        fragment = Fragment(
            html.h1("Title"),
            html.p("Paragraph 1"),
            html.p("Paragraph 2"),
        )
        container = html.div(fragment)
        expected_container = (
            "<div><h1>Title</h1><p>Paragraph 1</p><p>Paragraph 2</p></div>"
        )
        assert str(container) == expected_container

    with subtests.test("fragment with text content"):
        text_fragment = Fragment("Hello ", html.strong("world"), "!")
        assert str(text_fragment) == "Hello <strong>world</strong>!"

    with subtests.test("fragment with mixed content"):
        mixed = Fragment(
            "Text before",
            html.span("span content"),
            "Text after",
        )
        assert str(mixed) == "Text before<span>span content</span>Text after"

    with subtests.test("empty fragment"):
        empty = Fragment()
        assert str(empty) == ""

    with subtests.test("fragment in pretty mode"):
        pretty_fragment = Fragment(
            html.p("First"),
            html.p("Second"),
        )
        # Fragment itself doesn't add structure in pretty mode
        assert pretty_fragment.to_string(pretty=True) == "<p>First</p><p>Second</p>"

    with subtests.test("fragment inside container with pretty mode"):
        # Note: Fragment renders children without indentation to maintain transparency
        container_pretty = html.div(
            html.h1("Title"),
            Fragment(
                html.p("Paragraph 1"),
                html.p("Paragraph 2"),
            ),
        )
        expected_pretty = (
            "<div>\n"
            "\t<h1>\n"
            "\t\tTitle\n"
            "\t</h1>\n"
            "<p>Paragraph 1</p><p>Paragraph 2</p>"
            "</div>\n"
        )
        assert container_pretty.to_string(pretty=True) == expected_pretty

    with subtests.test("fragment maintains escaping behavior"):
        escaped_fragment = Fragment(
            "<script>alert('xss')</script>",
            html.p("safe content"),
        )
        assert (
            str(escaped_fragment)
            == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;<p>safe content</p>"
        )

    with subtests.test("fragment with callable children"):

        def get_content():
            return "dynamic content"

        callable_fragment = Fragment(
            html.p("static"),
            get_content,
        )
        assert str(callable_fragment) == "<p>static</p>dynamic content"

    with subtests.test("nested fragments"):
        nested = Fragment(
            html.div("outer"),
            Fragment(
                html.span("inner 1"),
                html.span("inner 2"),
            ),
        )
        assert str(nested) == "<div>outer</div><span>inner 1</span><span>inner 2</span>"


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

    # Test with no indentation (compact mode) - covers line 292 True branch
    # When indent_char="", output has no newlines, so everything accumulates in accu
    # and the final `if accu:` yields the accumulated content
    compact = html.div(html.p("Hello"), html.span("World"))
    compact_lines = list(compact.iter_lines(indent_char=""))
    assert compact_lines == ["<div><p>Hello</p><span>World</span></div>"]
    assert len(compact_lines) == 1

    # Test compact mode with single tag
    compact_single = html.p("text")
    assert list(compact_single.iter_lines(indent_char="")) == ["<p>text</p>"]

    # Test compact mode with void element
    compact_void = html.div(html.br())
    assert list(compact_void.iter_lines(indent_char="")) == ["<div><br/></div>"]


def test_iter_chunk():
    # Test basic chunking
    tag = html.div(
        html.p("Hello World"),
        html.p("Second paragraph"),
    )

    # Small chunk size to force multiple chunks
    chunks = list(tag.iter_chunk(chunk_size=10))
    # Verify we got multiple chunks
    assert len(chunks) > 1
    # Verify joining chunks gives the same result as to_string
    assert "".join(chunks) == tag.to_string()

    # Test with pretty mode
    pretty_chunks = list(tag.iter_chunk(chunk_size=20, pretty=True))
    assert len(pretty_chunks) > 1
    assert "".join(pretty_chunks) == tag.to_string(pretty=True)

    # Test with custom indent character
    indent_chunks = list(tag.iter_chunk(chunk_size=15, pretty=True, indent_char="  "))
    assert "".join(indent_chunks) == tag.to_string(pretty=True).replace("\t", "  ")

    # Test exact chunk size behavior
    simple = html.div("A" * 100)  # Create content longer than chunk_size
    chunks_50 = list(simple.iter_chunk(chunk_size=50))
    # Each chunk (except possibly the last) should be exactly 50 chars
    for chunk in chunks_50[:-1]:
        assert len(chunk) == 50
    # Verify reconstruction
    assert "".join(chunks_50) == simple.to_string()

    # Test with very large chunk size (should get single chunk)
    large_chunks = list(tag.iter_chunk(chunk_size=10000))
    assert len(large_chunks) == 1
    assert large_chunks[0] == tag.to_string()

    # Test empty tag
    empty = html.div()
    empty_chunks = list(empty.iter_chunk(chunk_size=10))
    assert "".join(empty_chunks) == "<div></div>"

    # Test nested complex structure
    nested = html.div(
        html.section(
            html.article(
                html.p("Content " * 20),
                html.p("More content " * 20),
            )
        )
    )
    nested_chunks = list(nested.iter_chunk(chunk_size=100))
    assert len(nested_chunks) > 1
    assert "".join(nested_chunks) == nested.to_string()

    # Test with void elements
    void_tag = html.div(html.br(), html.hr(), html.img(src="test.png"))
    void_chunks = list(void_tag.iter_chunk(chunk_size=15))
    assert "".join(void_chunks) == void_tag.to_string()

    # Test chunk size of 1 (edge case)
    tiny = html.p("Hi")
    tiny_chunks = list(tiny.iter_chunk(chunk_size=1))
    # Should have multiple single-character chunks
    assert len(tiny_chunks) > 1
    assert all(len(chunk) <= 1 for chunk in tiny_chunks)
    assert "".join(tiny_chunks) == tiny.to_string()


def test_parse(subtests):
    """Test HTML parsing functionality."""

    with subtests.test("basic single element"):
        result = parse("<div>Hello</div>")
        assert isinstance(result, Tag)
        assert result.name == "div"
        assert str(result) == "<div>Hello</div>"

    with subtests.test("nested elements"):
        html_str = "<div><p>Paragraph</p><span>Text</span></div>"
        result = parse(html_str)
        assert isinstance(result, Tag)
        assert result.name == "div"
        assert len(result.children) == 2
        assert str(result) == html_str

    with subtests.test("multiple root elements"):
        html_str = "<p>First</p><p>Second</p>"
        result = parse(html_str)
        assert isinstance(result, Fragment)
        assert str(result) == html_str

    with subtests.test("attributes"):
        result = parse('<div id="main" data-value="test">Content</div>')
        assert result["id"] == "main"
        assert result["data-value"] == "test"
        # Attributes are sorted, so check content
        assert 'id="main"' in str(result)
        assert 'data-value="test"' in str(result)
        assert ">Content</div>" in str(result)

    with subtests.test("class attribute"):
        result = parse('<div class="container primary">Content</div>')
        assert "container" in result.classes
        assert "primary" in result.classes
        # Classes are sorted when rendered
        assert 'class="container primary"' in str(result)

    with subtests.test("void elements"):
        html_str = "<div><br/><hr/></div>"
        result = parse(html_str)
        assert len(result.children) == 2
        # Parser normalizes to <br/>
        assert str(result) == html_str

    with subtests.test("self-closing tags"):
        html_str = '<img src="test.jpg" alt="Test"/>'
        result = parse(html_str)
        assert isinstance(result, Tag)
        assert result.name == "img"
        assert result["src"] == "test.jpg"
        assert result["alt"] == "Test"

    with subtests.test("text content"):
        result = parse("Just text")
        assert isinstance(result, Fragment)
        assert str(result) == "Just text"

    with subtests.test("mixed content"):
        html_str = "Text before<p>Paragraph</p>Text after"
        result = parse(html_str)
        assert isinstance(result, Fragment)
        assert len(result.children) == 3
        assert str(result) == html_str

    with subtests.test("entity decoding"):
        result = parse("<p>&lt;script&gt;alert('xss')&lt;/script&gt;</p>")
        # Entities should be decoded, then re-escaped when rendering
        output = str(result)
        assert "&lt;script&gt;" in output
        assert "alert(" in output
        assert "xss" in output

    with subtests.test("empty input"):
        result = parse("")
        assert isinstance(result, Fragment)
        assert str(result) == ""

    with subtests.test("whitespace only input"):
        result = parse("   \n\t  \n  ")
        assert isinstance(result, Fragment)
        assert str(result) == ""

    with subtests.test("complex nested structure"):
        html_str = '<div class="container"><header><h1>Title</h1></header><main><p>Content</p></main></div>'
        result = parse(html_str)
        assert isinstance(result, Tag)
        assert result.name == "div"
        assert "container" in result.classes
        # Should round-trip correctly
        assert str(result) == html_str

    with subtests.test("multiple classes"):
        html_str = '<span class="badge primary large active">Text</span>'
        result = parse(html_str)
        assert len(result.classes) == 4
        assert all(
            cls in result.classes for cls in ["badge", "primary", "large", "active"]
        )

    with subtests.test("boolean attributes"):
        html_str = '<input type="checkbox" checked/>'
        result = parse(html_str)
        assert result["type"] == "checkbox"
        assert result["checked"] is None  # Boolean attribute

    with subtests.test("whitespace preservation"):
        html_str = "<p>Line one\nLine two</p>"
        result = parse(html_str)
        assert "\n" in str(result)

    with subtests.test("script tag"):
        html_str = "<script>console.log('test');</script>"
        result = parse(html_str)
        assert result.name == "script"
        # Script content should be unescaped
        assert "console.log('test');" in str(result)

    with subtests.test("style tag"):
        html_str = "<style>body { margin: 0; }</style>"
        result = parse(html_str)
        assert result.name == "style"
        assert "margin: 0;" in str(result)

    with subtests.test("deeply nested"):
        html_str = "<div><div><div><p>Deep</p></div></div></div>"
        result = parse(html_str)
        assert str(result) == html_str

    with subtests.test("attributes without values"):
        html_str = "<button disabled>Click</button>"
        result = parse(html_str)
        assert result["disabled"] is None

    with subtests.test("full html document returns Page"):
        html_str = "<!DOCTYPE html><html><head><title>Test</title></head><body><p>Content</p></body></html>"
        result = parse(html_str)
        assert isinstance(result, Page)
        assert result.body is not None
        assert "Content" in str(result.body)
        assert result.head is not None
        assert "Test" in str(result.head)

    with subtests.test("html5 doctype"):
        html_str = "<!DOCTYPE html><html><head></head><body>Test</body></html>"
        result = parse(html_str)
        assert isinstance(result, Page)
        full_html = result.to_html5()
        assert full_html.startswith("<!DOCTYPE html>")

    with subtests.test("html4 doctype"):
        html_str = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd"><html><head></head><body>Test</body></html>'
        result = parse(html_str)
        assert isinstance(result, Page)
        full_html = result.to_html5()
        assert "HTML 4.01" in full_html
        assert full_html.startswith("<!DOCTYPE HTML PUBLIC")

    with subtests.test("html document with attributes"):
        html_str = '<html lang="en"><head></head><body>Content</body></html>'
        result = parse(html_str)
        assert isinstance(result, Page)
        assert result.html["lang"] == "en"

    with subtests.test("minimal html document"):
        html_str = "<html><body>Content</body></html>"
        result = parse(html_str)
        assert isinstance(result, Page)
        assert result.body is not None
        assert "Content" in str(result.body)

    with subtests.test("html with only head"):
        html_str = "<html><head><title>Title</title></head></html>"
        result = parse(html_str)
        assert isinstance(result, Page)
        assert result.head is not None
        assert "Title" in str(result.head)

    with subtests.test("self-closing tag with classes"):
        html_str = '<img class="logo primary" src="logo.png"/>'
        result = parse(html_str)
        assert isinstance(result, Tag)
        assert "logo" in result.classes
        assert "primary" in result.classes

    with subtests.test("html with text children"):
        # Tests branches where children are strings, not Tags
        html_str = "<html>text before<head></head>text between<body>content</body>text after</html>"
        result = parse(html_str)
        assert isinstance(result, Page)

    with subtests.test("html with other tag children"):
        # Tests branch where html has Tag children that aren't head or body
        html_str = "<html><footer>footer</footer><head></head><body>content</body><nav>nav</nav></html>"
        result = parse(html_str)
        assert isinstance(result, Page)
        # Should still extract head and body correctly
        assert result.body is not None
        assert result.head is not None

    with subtests.test("html with non-string attributes"):
        # Create a parser and manually add non-string attributes
        from tagz import TagParser

        parser = TagParser()
        parser.feed("<html><body>test</body></html>")
        parser.close()
        # Get the html tag before conversion
        html_tag = parser.root_elements[0]
        # Add a non-string attribute (callable)
        html_tag.attributes["data-func"] = lambda: "value"
        # Now get result - should filter out callable attribute
        result = parser.get_result()
        assert isinstance(result, Page)

    with subtests.test("head with text children"):
        # Tests branch where head has text children
        html_str = (
            "<html><head>text node<title>T</title>more text</head><body>b</body></html>"
        )
        result = parse(html_str)
        assert isinstance(result, Page)
        # Head tags should only include Tag children
        assert len(result.head.children) >= 1

    with subtests.test("malformed end tag"):
        # Tests branch where end tag is encountered with empty stack
        parser = TagParser()
        parser.feed("<div>content</div>")
        parser.feed("</extra>")  # Extra end tag
        parser.close()
        result = parser.get_result()
        assert isinstance(result, Tag)
