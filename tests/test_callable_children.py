import pytest
from html import escape
from tagz import html, ABSENT


def test_callable_child_str():
    def child():
        return "hello"

    tag = html.div(child)
    assert str(tag) == "<div>hello</div>"


def test_callable_child_tag():
    def child():
        return html.span("world")

    tag = html.div(child)
    assert str(tag) == "<div><span>world</span></div>"


def test_append_callable():
    def child():
        return "foo"

    tag = html.div()
    tag.append(child)
    assert str(tag) == "<div>foo</div>"


def test_single_evaluation():
    calls = []

    def child():
        calls.append(1)
        return "once"

    tag = html.div(child)
    result = str(tag)
    assert result == "<div>once</div>"
    assert calls == [1], "Callable child should be evaluated only once"


def test_callable_attribute_value():
    calls = []

    def value():
        calls.append(1)
        return "bar"

    tag = html.div(foo=value)
    # The callable is evaluated once and its result is escaped
    expected = f'<div foo="{escape("bar", quote=True)}"></div>'
    result = str(tag)
    assert result == expected
    assert calls == [1], (
        "Attribute value callback should be evaluated, and result escaped"
    )


def test_callable_attribute_and_child():
    attr_calls = []
    child_calls = []

    def attr():
        attr_calls.append(1)
        return "attrval"

    def child():
        child_calls.append(1)
        return "childval"

    tag = html.div(child, foo=attr)
    # The callable is evaluated once and its result is escaped
    expected = f'<div foo="{escape("attrval", quote=True)}">childval</div>'
    result = str(tag)
    assert result == expected
    assert attr_calls == [1]
    assert child_calls == [1]


def test_attr_tag_not_supported():
    def attr_tag():
        return html.span(bar="baz")

    tag = html.div(foo=attr_tag)
    # Should render the repr of the Tag, not HTML, and escape it
    result = str(tag)
    assert "<span" not in result
    assert 'foo="' in result
    assert "&lt;" in result and "&gt;" in result


def test_unescaped_attribute():
    tag = html.div(foo=123)
    assert str(tag) == '<div foo="123"></div>'
    tag = html.div(foo=None)
    assert str(tag) == "<div foo></div>"
    tag = html.div(foo=True)
    assert str(tag) == '<div foo="True"></div>'
    tag = html.div(foo="<b>unsafe</b>")
    # All attribute values must be escaped
    assert str(tag) == '<div foo="&lt;b&gt;unsafe&lt;/b&gt;"></div>'


def test_attribute_absent():
    present = True

    def attr():
        nonlocal present
        return "value" if present else ABSENT

    tag = html.div(test=attr)
    assert str(tag) == '<div test="value"></div>'

    present = False
    assert str(tag) == "<div></div>"

    present = True
    assert str(tag) == '<div test="value"></div>'
