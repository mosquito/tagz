"""Tests that run against both the sync (:mod:`tagz`) and async
(:mod:`tagz.aio`) flavours.

Each test takes the ``runtime`` fixture from ``conftest.py`` and unpacks it
into ``(tz, render)``. ``tz`` is the flavour module; ``render(obj)`` returns
the rendered HTML (calls ``to_html5`` for :class:`Page` and ``to_string``
for :class:`Tag`, wraps the async call in :func:`asyncio.run`).

Sync-specific tests (``parse``) stay in ``test_html.py``; async-specific
tests (coroutine children, async iterables, concurrent timing) stay in
``test_async_html.py``.
"""

from __future__ import annotations

from copy import copy

import pytest


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


def test_tag_creation(runtime, subtests):
    tz, render = runtime
    with subtests.test("Via Tag class"):
        tag = tz.Tag("div", classes=["container"], id="main")
        assert "container" in tag.classes
        assert tag.name == "div"
        assert tag["id"] == "main"
    with subtests.test("Via html factory"):
        tag = tz.html.div(classes=["container"], id="main")
        assert "container" in tag.classes
        assert tag.name == "div"
        assert tag["id"] == "main"


def test_tag_classes_manipulation(runtime, subtests):
    tz, _ = runtime
    tag = tz.html.div(classes=["new-class"])
    with subtests.test("classes on init"):
        assert tag.classes == {"new-class"}
    with subtests.test("add"):
        tag.classes.add("new-class")
        assert tag.classes == {"new-class"}
    with subtests.test("remove"):
        tag.classes.remove("new-class")
        assert "new-class" not in tag.classes
    with subtests.test("assign set"):
        tag.classes = {"class1", "class2"}
        assert tag.classes == {"class1", "class2"}
    with subtests.test("assign empty list"):
        tag.classes = []
        assert tag.classes == set()
    with subtests.test("assign space-separated string"):
        tag.classes = "class3 class4"
        assert tag.classes == {"class3", "class4"}
    with subtests.test("invalid type raises"):
        with pytest.raises(TypeError):
            tag.classes = 123


def test_void_tags(runtime, subtests):
    tz, render = runtime
    with subtests.test("br"):
        assert render(tz.html.br()) == "<br/>"
    with subtests.test("img with attrs"):
        out = render(tz.html.img(src="x.png", alt="An image"))
        assert out == '<img alt="An image" src="x.png"/>'
    with subtests.test("img with positional child rejected"):
        with pytest.raises(ValueError):
            tz.html.img("not allowed")
    with subtests.test("br.append rejected"):
        tag = tz.html.br()
        with pytest.raises(ValueError):
            tag.append(tz.html.span("nope"))


def test_html_class_factory(runtime):
    tz, render = runtime
    factory = tz.HTML({"custom-tag": {"__default_children__": ("Hello",)}})
    tag = factory.custom_tag()
    assert isinstance(tag, tz.Tag)
    assert render(tag) == "<custom-tag>Hello</custom-tag>"


# ---------------------------------------------------------------------------
# Basic rendering
# ---------------------------------------------------------------------------


def test_empty_div(runtime):
    tz, render = runtime
    assert render(tz.html.div()) == "<div></div>"


def test_text_child(runtime):
    tz, render = runtime
    assert render(tz.html.p("hello")) == "<p>hello</p>"


def test_nested(runtime):
    tz, render = runtime
    out = render(tz.html.div(tz.html.h1("Hi"), tz.html.p("body")))
    assert out == "<div><h1>Hi</h1><p>body</p></div>"


def test_tag_string_representation(runtime):
    tz, render = runtime
    tag = tz.html.p("Hello, World!", tz.html.a("go to index", "", href="/"), tz.html.i())
    assert render(tag) == '<p>Hello, World!<a href="/">go to index</a><i></i></p>'
    assert render(tag, pretty=True) == (
        '<p>\n\tHello, World!\n\t<a href="/">\n\t\tgo to index\n\t</a>\n\t<i>\n\t</i>\n</p>\n'
    )
    assert tz.html.my_custom_tag is tz.html.my_custom_tag
    assert render(tz.html.my_custom_tag()) == "<my-custom-tag></my-custom-tag>"
    assert render(tz.html.my_custom_tag("test")) == "<my-custom-tag>test</my-custom-tag>"


def test_pretty_deep_nesting(runtime):
    tz, render = runtime
    deep = tz.html.div(
        tz.html.section(
            tz.html.span(
                tz.html.article(
                    tz.html.p(
                        "Deeply nested paragraph.",
                        tz.html.span("With a span inside."),
                    )
                )
            )
        )
    )
    expected = (
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
    assert render(deep, pretty=True) == expected


# ---------------------------------------------------------------------------
# Escaping
# ---------------------------------------------------------------------------


def test_text_is_escaped(runtime):
    tz, render = runtime
    assert render(tz.html.p("<x&y>")) == "<p>&lt;x&amp;y&gt;</p>"


def test_attribute_value_is_escaped(runtime):
    tz, render = runtime
    out = render(tz.html.a("x", href='"><script>'))
    assert "<script>" not in out
    assert "&lt;" in out


def test_script_content_not_escaped(runtime):
    tz, render = runtime
    out = render(tz.html.script("""console.log(1 > 2 && 3 < 2 && "0" === '0');"""))
    assert out == """<script>console.log(1 > 2 && 3 < 2 && "0" === '0');</script>"""


def test_style_content_not_escaped(runtime):
    tz, render = runtime
    assert render(tz.html.style("body > div {color: red;}")) == "<style>body > div {color: red;}</style>"


def test_pre_escapes_special_chars(runtime):
    tz, render = runtime
    out = render(tz.html.pre("""console.log(1 > 2 && 3 < 2 && "0" === '0');"""))
    assert out == ("<pre>console.log(1 &gt; 2 &amp;&amp; 3 &lt; 2 &amp;&amp; &quot;0&quot; === &#x27;0&#x27;);</pre>")


# ---------------------------------------------------------------------------
# Attributes
# ---------------------------------------------------------------------------


def test_tag_attributes(runtime, subtests):
    tz, render = runtime
    with subtests.test("via constructor"):
        tag = tz.html.div(id="main", classes=["container", "fluid"], data_role="page")
        assert tag["id"] == "main"
        assert "container" in tag.classes
        assert tag["data-role"] == "page"
        assert render(tag) == '<div class="container fluid" data-role="page" id="main"></div>'
    with subtests.test("via item assignment"):
        tag = tz.html.div()
        tag["id"] = "main"
        tag["classes"] = ["container", "fluid"]
        tag["data-role"] = "page"
        assert render(tag) == '<div class="container fluid" data-role="page" id="main"></div>'
    with subtests.test("None renders as boolean"):
        assert render(tz.html.input(type="checkbox", checked=None)) == '<input checked type="checkbox"/>'
    with subtests.test("False removes"):
        assert render(tz.html.input(type="checkbox", checked=False)) == '<input type="checkbox"/>'
    with subtests.test("True renders as boolean"):
        assert render(tz.html.input(type="checkbox", disabled=True)) == '<input disabled type="checkbox"/>'
    with subtests.test("escape special chars"):
        tag = tz.html.div(title='This is a "quote" & test')
        assert render(tag) == '<div title="This is a &quot;quote&quot; &amp; test"></div>'
    with subtests.test("delete"):
        tag = tz.html.div(id="to-delete", classes=["temp"])
        del tag["id"]
        assert "id" not in tag.attributes
        assert render(tag) == '<div class="temp"></div>'
    with subtests.test("ABSENT removes"):
        tag = tz.html.div(test="value")
        assert tag["test"] == "value"
        tag["test"] = tz.ABSENT
        assert "test" not in tag.attributes
        assert render(tag) == "<div></div>"


def test_attribute_value_types(runtime, subtests):
    tz, render = runtime
    with subtests.test("int"):
        assert render(tz.html.div(foo=123)) == '<div foo="123"></div>'
    with subtests.test("None bool"):
        assert render(tz.html.div(foo=None)) == "<div foo></div>"
    with subtests.test("True bool"):
        assert render(tz.html.div(foo=True)) == "<div foo></div>"
    with subtests.test("HTML in value"):
        out = render(tz.html.div(foo="<b>unsafe</b>"))
        assert out == '<div foo="&lt;b&gt;unsafe&lt;/b&gt;"></div>'


def test_underscore_to_hyphen_in_attribute(runtime):
    tz, render = runtime
    out = render(tz.html.div("x", data_value="42"))
    assert 'data-value="42"' in out


def test_absent_attribute(runtime):
    tz, render = runtime
    out = render(tz.html.div("x", disabled=tz.ABSENT))
    assert "disabled" not in out


def test_tag_features(runtime):
    tz, render = runtime
    div = tz.html.div()
    assert render(div) == "<div></div>"
    div.append(tz.html.strong("hello"))
    assert render(div) == "<div><strong>hello</strong></div>"
    div["id"] = "foo"
    assert div["id"] == "foo"

    div = tz.html.div()
    div["custom"] = None
    assert render(div) == "<div custom></div>"

    div = tz.html.div(classes=["foo", "bar"])
    assert render(div) == '<div class="bar foo"></div>'


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


def test_classes_from_list(runtime):
    tz, render = runtime
    out = render(tz.html.div("x", classes=["foo", "bar"]))
    assert 'class="bar foo"' in out


def test_classes_from_string(runtime):
    tz, render = runtime
    out = render(tz.html.div("x", classes="a b"))
    assert 'class="a b"' in out


# ---------------------------------------------------------------------------
# Callable children
# ---------------------------------------------------------------------------


def test_callable_child_returning_string(runtime):
    tz, render = runtime
    assert render(tz.html.div(lambda: "hello")) == "<div>hello</div>"


def test_callable_attribute(runtime):
    tz, render = runtime
    out = render(tz.html.a("x", href=lambda: "/dest"))
    assert 'href="/dest"' in out


def test_callable_returning_tag(runtime):
    tz, render = runtime
    out = render(tz.html.div(lambda: tz.html.span("inner")))
    assert out == "<div><span>inner</span></div>"


# ---------------------------------------------------------------------------
# Fragment
# ---------------------------------------------------------------------------


def test_fragment(runtime, subtests):
    tz, render = runtime
    with subtests.test("multiple children"):
        out = render(
            tz.Fragment(
                tz.html.h1("Title"),
                tz.html.p("P1"),
                tz.html.p("P2"),
            )
        )
        assert out == "<h1>Title</h1><p>P1</p><p>P2</p>"

    with subtests.test("as child of another tag"):
        out = render(
            tz.html.div(
                tz.Fragment(
                    tz.html.h1("Title"),
                    tz.html.p("P1"),
                    tz.html.p("P2"),
                )
            )
        )
        assert out == "<div><h1>Title</h1><p>P1</p><p>P2</p></div>"

    with subtests.test("text content"):
        out = render(tz.Fragment("Hello ", tz.html.strong("world"), "!"))
        assert out == "Hello <strong>world</strong>!"

    with subtests.test("empty"):
        assert render(tz.Fragment()) == ""

    with subtests.test("pretty mode keeps inline"):
        out = render(tz.Fragment(tz.html.p("First"), tz.html.p("Second")), pretty=True)
        assert out == "<p>First</p><p>Second</p>"

    with subtests.test("inside container with pretty"):
        out = render(
            tz.html.div(
                tz.html.h1("Title"),
                tz.Fragment(tz.html.p("P1"), tz.html.p("P2")),
            ),
            pretty=True,
        )
        assert out == ("<div>\n\t<h1>\n\t\tTitle\n\t</h1>\n<p>P1</p><p>P2</p></div>\n")

    with subtests.test("escaping"):
        out = render(
            tz.Fragment(
                "<script>alert('xss')</script>",
                tz.html.p("safe"),
            )
        )
        assert out == "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;<p>safe</p>"

    with subtests.test("callable child"):
        out = render(tz.Fragment(tz.html.p("static"), lambda: "dynamic"))
        assert out == "<p>static</p>dynamic"

    with subtests.test("nested fragments"):
        out = render(
            tz.Fragment(
                tz.html.div("outer"),
                tz.Fragment(tz.html.span("inner 1"), tz.html.span("inner 2")),
            )
        )
        assert out == "<div>outer</div><span>inner 1</span><span>inner 2</span>"


# ---------------------------------------------------------------------------
# Raw
# ---------------------------------------------------------------------------


def test_raw(runtime):
    tz, render = runtime
    raw = tz.Raw("<custom>&hello;</custom>")
    assert render(raw) == "<custom>&hello;</custom>"
    assert render(tz.html.div(raw)) == "<div><custom>&hello;</custom></div>"
    # Raw content is never indented even in pretty mode.
    assert render(raw, pretty=True) == "<custom>&hello;</custom>"


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------


def test_style(runtime):
    tz, _ = runtime
    assert str(tz.Style(text_align="center", padding=0)) == "padding: 0; text-align: center;"
    assert str(tz.Style()) == ""
    style = tz.Style({"color": "red"})
    assert "color: red;" in str(style)
    underscored = tz.Style(font_size="12px", background_color="blue")
    assert "font-size: 12px;" in str(underscored)
    assert "background-color: blue;" in str(underscored)


def test_stylesheet(runtime):
    tz, _ = runtime
    sheet = tz.StyleSheet()
    sheet["body"] = tz.Style(background_color="#000000", color="#ffffff")
    sheet[("div", "a", "table")] = tz.Style(background_color="#111111", color="#cccccc")
    assert str(sheet) == (
        "body {background-color: #000000; color: #ffffff;}\ndiv, a, table {background-color: #111111; color: #cccccc;}"
    )


def test_style_attribute_value(runtime):
    tz, render = runtime
    out = render(tz.html.div("x", style=tz.Style(color="red", padding="0")))
    assert 'style="color: red; padding: 0;"' in out


def test_stylesheet_inside_style_tag(runtime):
    tz, render = runtime
    block = tz.html.style(tz.StyleSheet({"body": tz.Style(margin="0")}))
    assert "body {margin: 0;}" in render(block)


# ---------------------------------------------------------------------------
# Copy
# ---------------------------------------------------------------------------


def test_tag_copy(runtime):
    tz, _ = runtime
    tag = tz.html.div(name="foo")
    clone = copy(tag)
    clone["name"] = "bar"
    assert tag["name"] == "foo"
    assert clone["name"] == "bar"


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------


def test_page_renders(runtime):
    tz, render = runtime
    page = tz.Page(
        lang="en",
        body_element=tz.html.body(tz.html.h1("Hi")),
        head_elements=(tz.html.title("Demo"),),
    )
    out = render(page)
    assert out.startswith("<!doctype html>")
    assert "<title>Demo</title>" in out
    assert "<h1>Hi</h1>" in out


TEST_PAGE = """\
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
</html>"""


def test_webpage(runtime):
    tz, render = runtime
    page = tz.Page(
        lang="en",
        body_element=tz.html.body(
            tz.html.h1("Hello"),
            tz.html.div(tz.html.strong("world")),
            tz.html.a(
                "example link",
                tz.html.i("with italic text"),
                href="https://example.com/",
            ),
        ),
        head_elements=(
            tz.html.meta(charset="utf-8"),
            tz.html.meta(name="viewport", content="width=device-width, initial-scale=1"),
            tz.html.title("tagz example page"),
            tz.html.link(href="/static/css/bootstrap.min.css", rel="stylesheet"),
            tz.html.script(src="/static/js/bootstrap.bundle.min.js"),
            tz.html.style(
                tz.StyleSheet(
                    {
                        "body": tz.Style(padding="0", margin="0"),
                        (".container", ".container-fluid"): tz.Style(transition="opacity 600ms ease-in"),
                    }
                )
            ),
        ),
    )
    assert render(page, pretty=True).strip() == TEST_PAGE.strip()


# ---------------------------------------------------------------------------
# copy() must not double-escape — regression for the perf rewrite where the
# constructor re-escaped already-escaped strings (PR #9).
# ---------------------------------------------------------------------------


def test_copy_does_not_double_escape_text_children(runtime, subtests):
    tz, render = runtime
    with subtests.test("factory tag"):
        tag = tz.html.p("<x&y>")
        expected = "<p>&lt;x&amp;y&gt;</p>"
        assert render(tag) == expected
        assert render(copy(tag)) == expected
        assert render(tz.html.div(tag)) == f"<div>{expected}</div>"

    with subtests.test("base tag"):
        tag = tz.Tag("p", "<x&y>")
        expected = "<p>&lt;x&amp;y&gt;</p>"
        assert render(tag) == expected
        assert render(copy(tag)) == expected
        assert render(tz.html.div(tag)) == f"<div>{expected}</div>"

    with subtests.test("nested tags"):
        tag = tz.html.section(
            tz.html.p("<x&y>"),
            tz.html.span("a > b & c"),
        )
        expected = "<section><p>&lt;x&amp;y&gt;</p><span>a &gt; b &amp; c</span></section>"
        assert render(tag) == expected
        assert render(copy(tag)) == expected
        assert render(tz.html.div(tag)) == f"<div>{expected}</div>"


def test_copy_does_not_double_escape_fragment_children(runtime, subtests):
    tz, render = runtime
    with subtests.test("fragment"):
        fragment = tz.Fragment("<x&y>", tz.html.span("<a&b>"))
        expected = "&lt;x&amp;y&gt;<span>&lt;a&amp;b&gt;</span>"
        assert render(fragment) == expected
        assert render(copy(fragment)) == expected
        assert render(tz.html.div(fragment)) == f"<div>{expected}</div>"

    with subtests.test("nested fragment"):
        fragment = tz.Fragment(
            tz.html.p("<x&y>"),
            tz.Fragment("<a&b>", tz.html.strong("1 < 2")),
        )
        expected = "<p>&lt;x&amp;y&gt;</p>&lt;a&amp;b&gt;<strong>1 &lt; 2</strong>"
        assert render(fragment) == expected
        assert render(copy(fragment)) == expected
        assert render(tz.html.div(fragment)) == f"<div>{expected}</div>"


def test_copy_does_not_double_escape_classes_or_attributes(runtime, subtests):
    tz, render = runtime
    with subtests.test("classes"):
        tag = tz.html.div(classes=["a&b", "<danger>"])
        expected = '<div class="&lt;danger&gt; a&amp;b"></div>'
        assert render(tag) == expected
        assert render(copy(tag)) == expected
        assert render(tz.html.section(tag)) == f"<section>{expected}</section>"

    with subtests.test("attribute values"):
        tag = tz.html.a(
            "link",
            href="/search?q=<x>&sort=a&b",
            title='"quoted" & <unsafe>',
        )
        expected = (
            '<a href="/search?q=&lt;x&gt;&amp;sort=a&amp;b" '
            'title="&quot;quoted&quot; &amp; &lt;unsafe&gt;">link</a>'
        )
        assert render(tag) == expected
        assert render(copy(tag)) == expected
        assert render(tz.html.div(tag)) == f"<div>{expected}</div>"


def test_copy_preserves_unescaped_content(runtime, subtests):
    tz, render = runtime
    with subtests.test("raw"):
        raw = tz.Raw("<span>raw & trusted</span>")
        expected = "<span>raw & trusted</span>"
        assert render(raw) == expected
        assert render(copy(raw)) == expected
        assert render(tz.html.div(raw)) == f"<div>{expected}</div>"

    with subtests.test("script"):
        script = tz.html.script("if (a < b && c > d) { console.log('&'); }")
        expected = "<script>if (a < b && c > d) { console.log('&'); }</script>"
        assert render(script) == expected
        assert render(copy(script)) == expected
        assert render(tz.html.div(script)) == f"<div>{expected}</div>"

    with subtests.test("style"):
        style = tz.html.style("body > main { color: red; }")
        expected = "<style>body > main { color: red; }</style>"
        assert render(style) == expected
        assert render(copy(style)) == expected
        assert render(tz.html.div(style)) == f"<div>{expected}</div>"
