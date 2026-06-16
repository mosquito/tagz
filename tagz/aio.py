"""Async mirror of :mod:`tagz`. Same symbols, async render - change the import line and add ``await``.

Children and attributes may also be coroutines, awaitables, async-def functions, or async iterables.
See :doc:`docs/explanation/async-and-tagz` for the contract.
"""

from __future__ import annotations

import asyncio
import contextvars
import inspect
from collections.abc import AsyncIterator, Awaitable, Callable, Coroutine, Iterable
from copy import copy
from itertools import chain
from typing import Any, TypeVar

from . import sync
from .base import ABSENT, AbsentAttribute, HTML_DEFAULTS, HTMLBase, PageBase, Style, StyleSheet, TagBase, escape
from .sync import TagParser, data_uri, open_data_uri, parse


__all__ = (
    "ABSENT",
    "AbsentAttribute",
    "Fragment",
    "HTML",
    "Page",
    "Raw",
    "Style",
    "StyleSheet",
    "Tag",
    "TagInstance",
    "TagParser",
    "data_uri",
    "ensure_awaitable",
    "html",
    "open_data_uri",
    "parse",
)


R = TypeVar("R")


def ensure_awaitable(maybe_awaitable: Callable[..., R] | asyncio.Future[R] | Coroutine[None, None, R]) -> Awaitable[R]:
    """Coerce a callable, coroutine, or future to an :class:`Awaitable`.

    Sync callables are scheduled via ``loop.call_soon`` with a captured :mod:`contextvars` context.
    """
    if inspect.iscoroutinefunction(maybe_awaitable):
        return maybe_awaitable()
    if inspect.iscoroutine(maybe_awaitable):
        return maybe_awaitable
    if inspect.isawaitable(maybe_awaitable):
        return maybe_awaitable

    loop = asyncio.get_running_loop()
    future: asyncio.Future = loop.create_future()

    def _run() -> None:
        try:
            future.set_result(maybe_awaitable())
        except BaseException as exc:
            future.set_exception(exc)

    loop.call_soon(_run, context=contextvars.copy_context())
    return future


class Tag(TagBase):
    """Async HTML element. Sibling of :class:`tagz.Tag`; awaits any awaitable, iterates any ``__aiter__`` source."""

    def __str__(self) -> str:
        raise TypeError(
            "tagz.aio.Tag is async - use `await tag.to_string()` "
            "or `async for chunk in tag.iter_chunk()`, not `str(tag)`."
        )

    async def _format_attributes(self) -> str:
        """Invoke callable attribute values, await any awaitables, then format."""
        parts: list[str] = []
        for key, raw in sorted(self.attributes.items()):
            value: Any = raw
            if callable(value):
                value = value()
            if inspect.isawaitable(value):
                value = await value
            formatted = self._format_attribute(key, value)
            if formatted is not None:
                parts.append(formatted)
        return " ".join(parts)

    async def _format_tag_open(self) -> str:
        parts = [self.name]
        classes = self._format_classes()
        if classes:
            parts.append(classes)
        attrs = await self._format_attributes()
        if attrs:
            parts.append(attrs)
        opener = " ".join(parts)
        if self._void:
            return f"<{opener}/>"
        return f"<{opener}>"

    async def _format_tag_close(self) -> str:
        if self._void:
            return ""
        return f"</{self.name}>"

    async def _to_string(
        self,
        indent: str = "",
        indent_str: str = "",
    ) -> AsyncIterator[str]:
        yield indent
        yield await self._format_tag_open()

        if indent_str:
            yield "\n"

        if self._void:
            return

        escaped = self._escaped

        # _iter_children invokes sync callables; async-def returns coroutines - handled by isawaitable below.
        for child in self._iter_children():
            if inspect.isawaitable(child):
                child = await child
                if isinstance(child, str) and escaped:
                    child = escape(child)

            if hasattr(child, "__aiter__") and not isinstance(child, TagBase):
                async for item in child:
                    if inspect.isawaitable(item):
                        item = await item
                    if isinstance(item, str) and escaped:
                        item = escape(item)
                    async for chunk in self._emit_child(item, indent, indent_str):
                        yield chunk
                continue

            async for chunk in self._emit_child(child, indent, indent_str):
                yield chunk

        yield indent
        close = await self._format_tag_close()
        if close:
            yield close
        if indent_str:
            yield "\n"

    async def _emit_child(self, child: Any, indent: str, indent_str: str) -> AsyncIterator[str]:
        if isinstance(child, Tag):
            async for chunk in child._to_string(indent + indent_str, indent_str):
                yield chunk
            return
        if isinstance(child, sync.Tag):
            # Sync subtree inside an async tree - bridge through the sync generator.
            for chunk in child._to_string(indent + indent_str, indent_str):
                yield chunk
            return
        for chunk in self._iter_leaf(child, indent, indent_str):
            yield chunk

    async def to_string(self, pretty: bool = False) -> str:
        buf: list[str] = []
        async for frag in self._to_string("", "\t" if pretty else ""):
            buf.append(frag)
        return "".join(buf)

    async def iter_string(self, pretty: bool = False) -> AsyncIterator[str]:
        async for frag in self._to_string("", "\t" if pretty else ""):
            yield frag

    async def iter_chunk(
        self,
        chunk_size: int = 4096,
        pretty: bool = False,
        indent_char: str = "\t",
    ) -> AsyncIterator[str]:
        buffer = ""
        async for fragment in self._to_string("", indent_char if pretty else ""):
            buffer += fragment
            while len(buffer) >= chunk_size:
                yield buffer[:chunk_size]
                buffer = buffer[chunk_size:]
        if buffer:
            yield buffer

    async def iter_lines(self, indent_char: str = "\t") -> AsyncIterator[str]:
        accu = ""
        async for chunk in self._to_string("", indent_char):
            if "\n" in chunk:
                parts = chunk.split("\n")
                for part in parts[:-1]:
                    yield accu + part
                    accu = ""
                accu = parts[-1]
            else:
                accu += chunk
        if accu:
            yield accu


class TagInstance(Tag):
    """Async factory base. Sibling of :class:`tagz.TagInstance`."""

    __tag_name__: str
    __void__: bool = False
    __escaped__: bool = True
    __default_children__: Iterable[Any] = ()
    __default_attributes__: Any | None = None

    def __init__(
        self,
        *_children: Any,
        classes: Iterable[str] = (),
        **attributes: Any,
    ):
        attrs: dict = dict(self.__default_attributes__ or {})
        attrs.update(**attributes)
        children_iter: Iterable[Any] = (
            chain(self.__default_children__, _children) if self.__default_children__ else _children
        )
        materialised = tuple(copy(item) if isinstance(item, TagBase) else item for item in children_iter)
        TagBase.__init__(
            self,
            self.__tag_name__,
            *materialised,
            _void=self.__void__,
            _escaped=self.__escaped__,
            classes=classes,
            **attrs,
        )


class Fragment(Tag):
    """Async wrapper-less container - children render flat with no surrounding tag."""

    def __init__(self, *_children: Any, _escaped: bool = True):
        TagBase.__init__(self, "", *_children, _escaped=_escaped)

    async def _format_tag_open(self) -> str:
        return ""

    async def _format_tag_close(self) -> str:
        return ""

    async def _to_string(
        self,
        indent: str = "",
        indent_str: str = "",
    ) -> AsyncIterator[str]:
        async for chunk in Tag._to_string(self, "", ""):
            yield chunk


class Raw(Fragment):
    """Async :class:`tagz.Raw` - unescaped verbatim content."""

    def __init__(self, content: str):
        Fragment.__init__(self, content, _escaped=False)


class HTML(HTMLBase):
    """Async tag factory. Sibling of :class:`tagz.HTML`."""

    __tag_fabric__: type[TagInstance] = TagInstance
    _name_prefix: str = "AsyncTag"


#: Async tag factory, sharing :data:`tagz.base.HTML_DEFAULTS` with the sync factory.
html = HTML(HTML_DEFAULTS)


class Page(PageBase):
    """Async HTML5 document."""

    __html__ = html

    body: Tag
    head: Tag
    html: Tag

    async def to_html5(self, pretty: bool = False) -> str:
        return "".join((self.PREAMBLE, await self.html.to_string(pretty=pretty)))
