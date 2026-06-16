"""Sync-only tests for :mod:`tagz`.

Tests that exercise behaviour shared between :mod:`tagz` and
:mod:`tagz.aio` live in ``test_shared.py``. This file keeps only the
sync-specific surface: HTML parsing (:func:`tagz.parse` is sync-only) and
the void-element regression suite.
"""

from __future__ import annotations

from tagz import Fragment, Page, Tag, TagParser, parse


def test_parse(subtests):
    """Test HTML parsing functionality."""

    with subtests.test("basic single element"):
        result = parse("<div>Hello</div>")
        assert isinstance(result, Tag)
        assert result.name == "div"
        assert result.to_string() == "<div>Hello</div>"

    with subtests.test("nested elements"):
        html_str = "<div><p>Paragraph</p><span>Text</span></div>"
        result = parse(html_str)
        assert isinstance(result, Tag)
        assert result.name == "div"
        assert len(result.children) == 2
        assert result.to_string() == html_str

    with subtests.test("multiple root elements"):
        html_str = "<p>First</p><p>Second</p>"
        result = parse(html_str)
        assert isinstance(result, Fragment)
        assert result.to_string() == html_str

    with subtests.test("attributes"):
        result = parse('<div id="main" data-value="test">Content</div>')
        assert result["id"] == "main"
        assert result["data-value"] == "test"
        assert 'id="main"' in result.to_string()
        assert 'data-value="test"' in result.to_string()

    with subtests.test("class attribute"):
        result = parse('<div class="container primary">Content</div>')
        assert "container" in result.classes
        assert "primary" in result.classes
        assert 'class="container primary"' in result.to_string()

    with subtests.test("void elements"):
        html_str = "<div><br/><hr/></div>"
        result = parse(html_str)
        assert len(result.children) == 2
        assert result.to_string() == html_str

    with subtests.test("self-closing tags"):
        html_str = '<img src="test.jpg" alt="Test"/>'
        result = parse(html_str)
        assert isinstance(result, Tag)
        assert result.name == "img"

    with subtests.test("text content"):
        result = parse("Just text")
        assert isinstance(result, Fragment)
        assert result.to_string() == "Just text"

    with subtests.test("mixed content"):
        html_str = "Text before<p>Paragraph</p>Text after"
        result = parse(html_str)
        assert isinstance(result, Fragment)
        assert len(result.children) == 3
        assert result.to_string() == html_str

    with subtests.test("entity decoding"):
        result = parse("<p>&lt;script&gt;alert('xss')&lt;/script&gt;</p>")
        output = result.to_string()
        assert "&lt;script&gt;" in output
        assert "xss" in output

    with subtests.test("empty input"):
        result = parse("")
        assert isinstance(result, Fragment)
        assert result.to_string() == ""

    with subtests.test("whitespace only input"):
        result = parse("   \n\t  \n  ")
        assert isinstance(result, Fragment)
        assert result.to_string() == ""

    with subtests.test("complex nested structure"):
        html_str = '<div class="container"><header><h1>Title</h1></header><main><p>Content</p></main></div>'
        result = parse(html_str)
        assert isinstance(result, Tag)
        assert result.name == "div"
        assert result.to_string() == html_str

    with subtests.test("multiple classes"):
        html_str = '<span class="badge primary large active">Text</span>'
        result = parse(html_str)
        assert len(result.classes) == 4
        assert all(cls in result.classes for cls in ["badge", "primary", "large", "active"])

    with subtests.test("boolean attributes"):
        result = parse('<input type="checkbox" checked/>')
        assert result["type"] == "checkbox"
        assert result["checked"] is None

    with subtests.test("whitespace preservation"):
        result = parse("<p>Line one\nLine two</p>")
        assert "\n" in result.to_string()

    with subtests.test("script tag"):
        result = parse("<script>console.log('test');</script>")
        assert result.name == "script"
        assert "console.log('test');" in result.to_string()

    with subtests.test("style tag"):
        result = parse("<style>body { margin: 0; }</style>")
        assert result.name == "style"
        assert "margin: 0;" in result.to_string()

    with subtests.test("deeply nested"):
        html_str = "<div><div><div><p>Deep</p></div></div></div>"
        assert parse(html_str).to_string() == html_str

    with subtests.test("attributes without values"):
        result = parse("<button disabled>Click</button>")
        assert result["disabled"] is None

    with subtests.test("full html document returns Page"):
        result = parse("<!DOCTYPE html><html><head><title>Test</title></head><body><p>Content</p></body></html>")
        assert isinstance(result, Page)
        assert "Content" in result.body.to_string()
        assert "Test" in result.head.to_string()

    with subtests.test("html5 doctype"):
        result = parse("<!DOCTYPE html><html><head></head><body>Test</body></html>")
        assert result.to_html5().startswith("<!DOCTYPE html>")

    with subtests.test("html4 doctype"):
        result = parse(
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
            '"http://www.w3.org/TR/html4/strict.dtd">'
            "<html><head></head><body>Test</body></html>"
        )
        assert isinstance(result, Page)
        full = result.to_html5()
        assert full.startswith("<!DOCTYPE HTML PUBLIC")

    with subtests.test("html document with attributes"):
        result = parse('<html lang="en"><head></head><body>Content</body></html>')
        assert result.html["lang"] == "en"

    with subtests.test("minimal html document"):
        result = parse("<html><body>Content</body></html>")
        assert "Content" in result.body.to_string()

    with subtests.test("html with only head"):
        result = parse("<html><head><title>Title</title></head></html>")
        assert "Title" in result.head.to_string()

    with subtests.test("self-closing tag with classes"):
        result = parse('<img class="logo primary" src="logo.png"/>')
        assert "logo" in result.classes
        assert "primary" in result.classes

    with subtests.test("html with text children"):
        result = parse("<html>text before<head></head>text between<body>content</body>text after</html>")
        assert isinstance(result, Page)

    with subtests.test("html with other tag children"):
        result = parse("<html><footer>footer</footer><head></head><body>content</body><nav>nav</nav></html>")
        assert isinstance(result, Page)

    with subtests.test("html with non-string attributes"):
        parser = TagParser()
        parser.feed("<html><body>test</body></html>")
        parser.close()
        html_tag = parser.root_elements[0]
        html_tag.attributes["data-func"] = lambda: "value"
        assert isinstance(parser.get_result(), Page)

    with subtests.test("head with text children"):
        result = parse("<html><head>text node<title>T</title>more text</head><body>b</body></html>")
        assert isinstance(result, Page)
        assert len(result.head.children) >= 1

    with subtests.test("malformed end tag"):
        parser = TagParser()
        parser.feed("<div>content</div></extra>")
        parser.close()
        assert isinstance(parser.get_result(), Tag)


# All HTML5 void elements (no end tag).
VOID_ELEMENTS = (
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
)


def test_parse_void_without_slash_regression(subtests):
    """Regression: void elements written without a trailing slash must not
    swallow following siblings as children."""

    with subtests.test("img followed by sibling, no slash"):
        result = parse('<div><img src="x.webp" alt="test"><p>hello</p></div>')
        assert isinstance(result, Tag)
        assert len(result.children) == 2
        img, p = result.children
        assert isinstance(img, Tag) and img.name == "img" and img._void
        assert isinstance(p, Tag) and p.name == "p"

    with subtests.test("img followed by sibling, with whitespace"):
        result = parse('<div><img src="x.webp" alt="test">\n<p>hello</p></div>')
        tags = [c for c in result.children if isinstance(c, Tag)]
        assert [t.name for t in tags] == ["img", "p"]

    with subtests.test("leading/trailing whitespace around tags"):
        result = parse('<div>\n<img src="x.webp" alt="test">\n<p>hello</p>\n</div>')
        tags = [c for c in result.children if isinstance(c, Tag)]
        assert [t.name for t in tags] == ["img", "p"]

    with subtests.test("img followed by header"):
        result = parse('<div><img src="x.webp" alt="test"><header>text</header></div>')
        tags = [c for c in result.children if isinstance(c, Tag)]
        assert [t.name for t in tags] == ["img", "header"]

    with subtests.test("lone img without slash"):
        result = parse('<img src="x.webp" alt="test">')
        assert isinstance(result, Tag) and result.name == "img"

    with subtests.test("consecutive void elements"):
        result = parse("<div><br><br><hr></div>")
        tags = [c for c in result.children if isinstance(c, Tag)]
        assert [t.name for t in tags] == ["br", "br", "hr"]

    with subtests.test("void element followed by text"):
        result = parse("<div><br>after</div>")
        assert "after" in result.to_string()
        tags = [c for c in result.children if isinstance(c, Tag)]
        assert [t.name for t in tags] == ["br"]

    with subtests.test("input followed by label"):
        result = parse('<div><input type="text"><label>Name</label></div>')
        tags = [c for c in result.children if isinstance(c, Tag)]
        assert [t.name for t in tags] == ["input", "label"]

    with subtests.test("multiple void siblings in head"):
        result = parse('<head><meta charset="utf-8"><link rel="stylesheet" href="a.css"><title>T</title></head>')
        tags = [c for c in result.children if isinstance(c, Tag)]
        assert [t.name for t in tags] == ["meta", "link", "title"]

    with subtests.test("nested containers with void elements"):
        result = parse("<div><section><img src=a><p>x</p></section><hr><footer>y</footer></div>")
        top = [c for c in result.children if isinstance(c, Tag)]
        assert [t.name for t in top] == ["section", "hr", "footer"]

    with subtests.test("every void element type with a sibling, no slash"):
        for name in VOID_ELEMENTS:
            result = parse(f"<div><{name}><p>sibling</p></div>")
            tags = [c for c in result.children if isinstance(c, Tag)]
            assert [t.name for t in tags] == [name, "p"], name
            assert tags[0]._void, name


def test_parse_void_slash_equivalence(subtests):
    """``<img ...>`` and ``<img ... />`` must parse to the same thing."""

    pairs = [
        ('<img src="x.webp" alt="test">', '<img src="x.webp" alt="test" />'),
        ("<div><br><p>x</p></div>", "<div><br/><p>x</p></div>"),
        (
            '<div><input name="a"><label>L</label></div>',
            '<div><input name="a" /><label>L</label></div>',
        ),
        (
            '<head><meta charset="utf-8"><title>T</title></head>',
            '<head><meta charset="utf-8" /><title>T</title></head>',
        ),
    ]
    for no_slash, with_slash in pairs:
        with subtests.test(no_slash=no_slash):
            assert parse(no_slash).to_string() == parse(with_slash).to_string()

    with subtests.test("every void element type, slash vs no slash"):
        for name in VOID_ELEMENTS:
            no_slash = f'<div><{name} class="c" data-x="1"><p>x</p></div>'
            with_slash = f'<div><{name} class="c" data-x="1" /><p>x</p></div>'
            assert parse(no_slash).to_string() == parse(with_slash).to_string(), name

    with subtests.test("void element attributes and classes preserved"):
        result = parse('<img class="logo big" src="a.png" alt="hi"><p>next</p>')
        assert isinstance(result, Fragment)
        img = result.children[0]
        assert isinstance(img, Tag) and img.name == "img"
        assert img.classes == {"logo", "big"}


def test_parse_void_roundtrip(subtests):
    """Void elements without slashes round-trip to canonical self-closed form."""

    cases = [
        (
            '<div><img src="x.webp" alt="test"><p>hello</p></div>',
            '<div><img alt="test" src="x.webp"/><p>hello</p></div>',
        ),
        ("<br><br><hr>", "<br/><br/><hr/>"),
        (
            '<input type="text"><label>x</label>',
            '<input type="text"/><label>x</label>',
        ),
    ]
    for source, expected in cases:
        with subtests.test(source=source):
            assert parse(source).to_string() == expected
