from copy import copy

import pytest

from tagz import HTML, Page, Style, Tag, html, StyleSheet


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


def test_tag_creation():
    tag = Tag("div", classes=["container"], id="main")
    assert "container" in tag.classes
    assert tag.name == "div"
    assert tag["id"] == "main"

    tag = html.div(classes=["container"], id="main")
    assert "container" in tag.classes
    assert tag.name == "div"
    assert tag["id"] == "main"


def test_tag_string_representation():
    tag = html.p("Hello, World!", html.a("go to index", "", href="/"), html.i())
    assert str(tag) == '<p>Hello, World!<a href="/">go to index</a><i/></p>'
    assert tag.to_string(pretty=True) == (
        '<p>\n\tHello, World!\n\t<a href="/">\n\t\tgo to index\n\t</a>\n\t<i/>\n</p>\n'
    )
    assert html.my_custom_tag is html.my_custom_tag
    assert str(html.my_custom_tag()) == "<my-custom-tag/>"
    assert str(html.my_custom_tag("test")) == "<my-custom-tag>test</my-custom-tag>"


def test_html_generation(sample_html_page):
    html_str = sample_html_page.to_html5()
    assert "<!doctype html>" in html_str
    assert "<html lang=\"en\">" in html_str
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


def test_tag_features():
    div = html.div()

    assert str(div) == "<div/>"
    div.append(html.strong("hello"))

    assert str(div) == "<div><strong>hello</strong></div>"
    div["id"] = "foo"

    assert div["id"] == "foo"
    div["custom_attr"] = " custom value "

    div = html.div()
    div["custom"] = None
    assert str(div) == "<div custom/>"

    div = html.div(classes=["foo", "bar"])
    assert str(div) == '<div class="bar foo"/>'

    div = html.div()
    assert repr(div) == "<div/>"

    div = html.div("Hello")
    assert repr(div) == "<div>...</div>"


def test_style():
    assert str(Style(text_align="center", padding=0)) == 'padding: 0; text-align: center;'

    style = Style()
    assert str(style) == ''

    style['padding'] = 0
    assert str(style) == "padding: 0;"

    style['margin'] = 0
    assert str(style) == 'margin: 0; padding: 0;'

    assert str(
        html.div("red", style=Style(color="#ff0000"))
    ) == (
        '<div style="color: #ff0000;">red</div>'
    )


def test_stylesheet():
    style_sheet = StyleSheet()
    style_sheet['body'] = Style(background_color="#000000", color="#ffffff")
    style_sheet[('div', 'a', 'table')] = Style(background_color="#111111", color="#cccccc")

    assert str(style_sheet) == (
        'body {background-color: #000000; color: #ffffff;}\n'
        'div, a, table {background-color: #111111; color: #cccccc;}'
    )


def test_tag_copy():
    tag = html.div(name='foo')
    clone = copy(tag)
    clone['name'] = 'bar'

    assert tag != clone
    assert tag['name'] != clone['name']
    assert tag['name'] == 'foo'
    assert clone['name'] == 'bar'

