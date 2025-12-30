import pytest
from tagz import Tag, html

def test_callable_child_str():
    def child():
        return "hello"
    tag = Tag("div", child)
    assert str(tag) == "<div>hello</div>"

def test_callable_child_tag():
    def child():
        return html.span("world")
    tag = Tag("div", child)
    assert str(tag) == "<div><span>world</span></div>"

def test_append_callable():
    def child():
        return "foo"
    tag = Tag("div")
    tag.append(child)
    assert str(tag) == "<div>foo</div>"

def test_recursive_callable():
    def inner():
        return "deep"
    def outer():
        return html.span(inner)
    tag = Tag("div", outer)
    assert str(tag) == "<div><span>deep</span></div>"

def test_double_recursive_callable():
    def leaf():
        return "leaf"
    def mid():
        return html.b(leaf)
    def top():
        return html.i(mid)
    tag = Tag("div", top)
    assert str(tag) == "<div><i><b>leaf</b></i></div>"

def test_single_evaluation():
    calls = []
    def child():
        calls.append(1)
        return "once"
    tag = Tag("div", child)
    result = str(tag)
    assert result == "<div>once</div>"
    assert calls == [1], "Callable child should be evaluated only once"

def test_too_deep_recursion():
    import sys
    sys.setrecursionlimit(50)
    def deep():
        return html.div(deep)
    tag = Tag("div", deep)
    with pytest.raises(RecursionError):
        str(tag)
    sys.setrecursionlimit(1000)
