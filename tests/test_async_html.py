"""Async-specific tests for :mod:`tagz.aio`.

Tests that work identically for sync and async live in ``test_shared.py``.
This file keeps the surface that only exists in the async build:
coroutine / awaitable / async-iterable children, async attribute values,
``str()`` raising on async tags, re-render error wrapping for exhausted
coroutines, and concurrency-timing assertions.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator

import pytest

from tagz.aio import ABSENT, Fragment, Page, html


# ---------------------------------------------------------------------------
# str(async_tag) is forbidden
# ---------------------------------------------------------------------------


def test_str_async_tag_raises():
    with pytest.raises(TypeError, match="async"):
        str(html.div("x"))


# ---------------------------------------------------------------------------
# Coroutine children
# ---------------------------------------------------------------------------


async def _name():
    await asyncio.sleep(0)
    return "Ada"


def test_coroutine_as_text_child():
    tag = html.div("Hello, ", _name(), "!")
    assert asyncio.run(tag.to_string()) == "<div>Hello, Ada!</div>"


def test_coroutine_returning_tag():
    async def make_card():
        return html.span("inner")

    tag = html.div(make_card())
    assert asyncio.run(tag.to_string()) == "<div><span>inner</span></div>"


def test_coroutine_returning_tag_with_async_child():
    """A resolved coroutine may produce a Tag whose own children are async."""

    async def inner_text():
        return "deep"

    async def outer():
        return html.span(inner_text())

    tag = html.div(outer())
    assert asyncio.run(tag.to_string()) == "<div><span>deep</span></div>"


# ---------------------------------------------------------------------------
# Async-def functions are re-callable across renders
# ---------------------------------------------------------------------------


def test_async_fn_child_renderable_twice():
    calls = [0]

    async def name():
        calls[0] += 1
        return "Ada"

    tag = html.div(name)
    assert asyncio.run(tag.to_string()) == "<div>Ada</div>"
    assert asyncio.run(tag.to_string()) == "<div>Ada</div>"
    assert calls[0] == 2


# ---------------------------------------------------------------------------
# asyncio.Task / Future children
# ---------------------------------------------------------------------------


def test_task_as_child():
    async def go():
        task = asyncio.create_task(_name())
        return await html.div("Hi, ", task, "!").to_string()

    assert asyncio.run(go()) == "<div>Hi, Ada!</div>"


# ---------------------------------------------------------------------------
# Async iterables
# ---------------------------------------------------------------------------


def test_async_iterable_yields_tags():
    async def items():
        for label in ("a", "b", "c"):
            yield html.li(label)

    out = asyncio.run(html.ul(items()).to_string())
    assert out == "<ul><li>a</li><li>b</li><li>c</li></ul>"


def test_async_iterable_yields_strings_and_tags_mixed():
    async def items():
        yield "first "
        yield html.strong("BOLD")
        yield " last"

    out = asyncio.run(html.span(items()).to_string())
    assert out == "<span>first <strong>BOLD</strong> last</span>"


# ---------------------------------------------------------------------------
# Async attribute values
# ---------------------------------------------------------------------------


def test_async_attribute_coroutine():
    async def fetch_href():
        return "/dest"

    out = asyncio.run(html.a("link", href=fetch_href()).to_string())
    assert 'href="/dest"' in out


def test_async_attribute_callable():
    async def fetch_class():
        return "ok"

    out = asyncio.run(html.div("x", data_state=fetch_class).to_string())
    assert 'data-state="ok"' in out


def test_async_attribute_returning_absent():
    async def maybe():
        return ABSENT

    out = asyncio.run(html.div("x", disabled=maybe()).to_string())
    assert "disabled" not in out


# ---------------------------------------------------------------------------
# Escape on async-resolved values
# ---------------------------------------------------------------------------


def test_async_value_string_is_escaped():
    async def evil():
        return "<script>alert('xss')</script>"

    out = asyncio.run(html.p(evil()).to_string())
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_async_attribute_string_is_escaped():
    async def evil():
        return '"><script>'

    out = asyncio.run(html.a("x", href=evil()).to_string())
    assert "<script>" not in out
    assert "&lt;" in out


# ---------------------------------------------------------------------------
# Fragment with async children
# ---------------------------------------------------------------------------


def test_fragment_with_async_children():
    frag = Fragment(_name(), "!")
    assert asyncio.run(frag.to_string()) == "Ada!"


# ---------------------------------------------------------------------------
# Streaming with async children
# ---------------------------------------------------------------------------


async def _drain(it: AsyncIterator[str]) -> list[str]:
    return [c async for c in it]


def test_iter_chunk_assembles_correctly():
    tag = html.div("Hello, ", _name(), "!")

    async def go():
        return await _drain(tag.iter_chunk(chunk_size=8))

    chunks = asyncio.run(go())
    assert "".join(chunks) == "<div>Hello, Ada!</div>"


def test_iter_lines_pretty_format():
    tag = html.div(html.p("x"), html.p(_name()))

    async def go():
        return await _drain(tag.iter_lines())

    lines = asyncio.run(go())
    assert all("\n" not in line for line in lines)
    assert lines[0] == "<div>"
    assert lines[-1] == "</div>"
    assert any("Ada" in line for line in lines)


def test_iter_string_yields_fragments():
    tag = html.div(html.p(_name()))

    async def go():
        return await _drain(tag.iter_string())

    parts = asyncio.run(go())
    assert "".join(parts) == "<div><p>Ada</p></div>"


# ---------------------------------------------------------------------------
# Page with async children
# ---------------------------------------------------------------------------


def test_page_renders_with_async_children():
    page = Page(
        lang="en",
        body_element=html.body(html.h1(_name())),
        head_elements=(html.title("Demo"),),
    )
    out = asyncio.run(page.to_html5())
    assert out.startswith("<!doctype html>")
    assert "Ada" in out


# ---------------------------------------------------------------------------
# Re-render and coroutine reuse
# ---------------------------------------------------------------------------


def test_re_render_with_raw_coroutine_raises():
    tag = html.div(_name())

    async def go():
        await tag.to_string()
        await tag.to_string()

    with pytest.raises(RuntimeError, match="already awaited"):
        asyncio.run(go())


def test_re_render_with_async_callable_works():
    tag = html.div(_name)
    assert asyncio.run(tag.to_string()) == "<div>Ada</div>"
    assert asyncio.run(tag.to_string()) == "<div>Ada</div>"


# ---------------------------------------------------------------------------
# Sync subtree mixed into async tree
# ---------------------------------------------------------------------------


def test_sync_subtree_inside_async_tree_renders():
    import tagz

    sync_inner = tagz.html.span("sync")
    async_outer = html.div("before ", sync_inner, " after")
    out = asyncio.run(async_outer.to_string())
    assert out == "<div>before <span>sync</span> after</div>"


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------


def test_concurrent_external_gather_overlaps_awaits():
    """When the user starts Tasks externally, awaits inside render are basically free."""

    async def slow(label: str, delay: float):
        await asyncio.sleep(delay)
        return label

    async def go():
        t0 = time.perf_counter()
        tasks = [asyncio.create_task(slow(f"t{i}", 0.1)) for i in range(3)]
        tag = html.div(*(html.p(t) for t in tasks))
        out = await tag.to_string()
        return out, time.perf_counter() - t0

    out, elapsed = asyncio.run(go())
    assert "t0" in out and "t2" in out
    assert elapsed < 0.25, f"expected concurrent but took {elapsed:.3f}s"


def test_serial_render_takes_sum_of_awaits():
    """Without external Tasks, serial document-order awaits sum up."""

    async def slow(label: str, delay: float):
        await asyncio.sleep(delay)
        return label

    async def go():
        t0 = time.perf_counter()
        tag = html.div(*(html.p(slow(f"t{i}", 0.05)) for i in range(3)))
        await tag.to_string()
        return time.perf_counter() - t0

    elapsed = asyncio.run(go())
    assert elapsed >= 0.13, f"expected ~150ms serial, got {elapsed:.3f}s"
