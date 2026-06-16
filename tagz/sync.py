"""Sync implementation. Re-exported from :mod:`tagz`."""

from __future__ import annotations

import base64
import mimetypes
from copy import copy
from html.parser import HTMLParser
from itertools import chain
from pathlib import Path
from collections.abc import Iterable, Iterator, Mapping
from typing import Any

from .base import (
    ABSENT,
    AbsentAttribute,
    AttributeType,
    ChildType,
    HTML_DEFAULTS,
    HTMLBase,
    PageBase,
    Style,
    StyleSheet,
    TagBase,
)


__all__ = (
    "ABSENT",
    "AbsentAttribute",
    "AttributeType",
    "ChildType",
    "Fragment",
    "HTML",
    "HTML_DEFAULTS",
    "HTMLBase",
    "Page",
    "PageBase",
    "Raw",
    "Style",
    "StyleSheet",
    "Tag",
    "TagBase",
    "TagInstance",
    "TagParser",
    "data_uri",
    "html",
    "open_data_uri",
    "parse",
)


class Tag(TagBase):
    """Sync HTML element. Sync sibling of :class:`tagz.aio.Tag`."""

    def _format_attributes(self) -> str:
        parts: list[str] = []
        for key, value in sorted(self.attributes.items()):
            v = value() if callable(value) else value
            formatted = self._format_attribute(key, v)
            if formatted is not None:
                parts.append(formatted)
        return " ".join(parts)

    def _make_parts(self) -> Iterator[str]:
        yield self.name
        classes = self._format_classes()
        if classes:
            yield classes
        attributes = self._format_attributes()
        if attributes:
            yield attributes

    def _format_tag_open(self) -> Iterable[str]:
        yield "<"
        yield " ".join(self._make_parts())
        if self._void:
            yield "/>"
            return
        yield ">"

    def _format_tag_close(self) -> Iterable[str]:
        if self._void:
            return
        yield f"</{self.name}>"

    def __repr__(self) -> str:
        parts = ["".join(self._format_tag_open())]
        if self._void:
            return parts[0]
        parts.append("..." if self.children else "")
        parts.append(f"</{self.name}>")
        return "".join(parts)

    def _emit_child(self, child: Any, indent: str, indent_str: str) -> Iterator[str]:
        if isinstance(child, Tag):
            yield from child._to_string(indent + indent_str, indent_str)
        else:
            yield from self._iter_leaf(child, indent, indent_str)

    def _to_string(self, indent: str = "", indent_str: str = "") -> Iterable[str]:
        """Yield HTML fragments in document order."""
        yield indent
        yield from self._format_tag_open()

        if indent_str:
            yield "\n"

        if self._void:
            yield from self._format_tag_close()
            return

        for child in self._iter_children():
            yield from self._emit_child(child, indent, indent_str)

        yield indent
        yield from self._format_tag_close()
        if indent_str:
            yield "\n"

    def __str__(self) -> str:
        import warnings

        warnings.warn(
            "str(tag) is deprecated; call tag.to_string() explicitly.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.to_string()

    def to_string(self, pretty: bool = False) -> str:
        """Render to a complete HTML string. ``pretty=True`` indents and line-breaks."""
        return "".join(self.iter_string(pretty=pretty))

    def iter_string(self, pretty: bool = False) -> Iterator[str]:
        """Yield rendered HTML as small fragments. For streaming, prefer :meth:`iter_lines` or :meth:`iter_chunk`."""
        yield from self._to_string("", "\t" if pretty else "")

    def iter_lines(self, indent_char: str = "\t") -> Iterator[str]:
        """Yield pretty-printed HTML line by line (no trailing ``\\n``)."""
        accu = ""
        for chunk in self._to_string("", indent_char):
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

    def iter_chunk(self, chunk_size: int = 4096, pretty: bool = False, indent_char: str = "\t") -> Iterator[str]:
        """Yield ~``chunk_size`` character chunks for streaming into buffered I/O."""
        buffer = ""
        for fragment in self._to_string("", indent_char if pretty else ""):
            buffer += fragment
            while len(buffer) >= chunk_size:
                yield buffer[:chunk_size]
                buffer = buffer[chunk_size:]
        if buffer:
            yield buffer


class TagInstance(Tag):
    """Base for factory-produced element classes (``html.div`` → ``TagDiv``)."""

    __tag_name__: str
    __void__: bool = False
    __escaped__: bool = True
    __default_children__: Iterable[str | Tag] = ()
    __default_attributes__: Mapping[str, str] | None = None

    def __init__(
        self,
        *_children: ChildType,
        classes: Iterable[str] = (),
        **attributes: AttributeType,
    ):
        attrs: dict[str, AttributeType] = dict(self.__default_attributes__ or {})
        attrs.update(**attributes)
        children_iter = chain(self.__default_children__, _children) if self.__default_children__ else _children
        _children = tuple(item if isinstance(item, str) else copy(item) for item in children_iter)

        super().__init__(
            self.__tag_name__,
            *_children,
            _void=self.__void__,
            _escaped=self.__escaped__,
            classes=classes,
            **attrs,
        )


class HTML(HTMLBase):
    """Sync tag factory. ``html.div`` and ``html["div"]`` return the same :class:`TagInstance` subclass."""

    __tag_fabric__: type[TagInstance] = TagInstance
    _name_prefix: str = "Tag"


#: Default sync factory configured with HTML5 void / unescaped elements.
html = HTML(HTML_DEFAULTS)


class Fragment(Tag):
    """Wrapper-less container - renders children inline with no surrounding tag."""

    def __init__(self, *_children: ChildType, _escaped: bool = True):
        super().__init__("", *_children, _escaped=_escaped)

    def _format_tag_open(self) -> Iterator[str]:
        yield ""

    def _format_tag_close(self) -> Iterator[str]:
        yield ""

    def _to_string(self, indent: str = "", indent_str: str = "") -> Iterable[str]:
        return super()._to_string("", "")


class Raw(Fragment):
    """Wrapper-less verbatim content. **No escaping** - use only with trusted input (XSS risk otherwise)."""

    def __init__(self, content: str):
        super().__init__("", content, _escaped=False)


class Page(PageBase):
    """Sync HTML5 document."""

    __html__ = html

    body: Tag
    head: Tag
    html: Tag

    def to_html5(self, pretty: bool = False) -> str:
        """Render document including ``PREAMBLE``."""
        return "".join((self.PREAMBLE, self.html.to_string(pretty=pretty)))


class TagParser(HTMLParser):
    """Builds :class:`Tag` objects from HTML strings. Most users should call :func:`parse` instead."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root_elements: list[Tag | str] = []
        self.stack: list[Tag] = []
        self.doctype: str | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_attrs: dict[str, Any] = {}
        classes: list[str] = []

        for key, value in attrs:
            if key == "class":
                classes.extend(value.split() if value else [])
            else:
                tag_attrs[key] = value if value is not None else None

        tag_obj = html[tag](**tag_attrs)
        if classes:
            tag_obj.classes = set(classes)

        if self.stack:
            self.stack[-1].append(tag_obj)
        else:
            self.root_elements.append(tag_obj)

        # Void elements cannot have children and have no end tag, so they must
        # not be pushed onto the stack. Otherwise the next start tag would be
        # appended as a child of the void element, which is invalid.
        if tag_obj._void:
            return

        self.stack.append(tag_obj)

    def handle_endtag(self, tag: str) -> None:
        """Handle closing tag."""
        if self.stack:
            self.stack.pop()

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Handle self-closing/void tag."""
        tag_attrs: dict[str, Any] = {}
        classes: list[str] = []

        for key, value in attrs:
            if key == "class":
                classes.extend(value.split() if value else [])
            else:
                tag_attrs[key] = value if value is not None else None

        tag_obj = html[tag](**tag_attrs)
        if classes:
            tag_obj.classes = set(classes)

        if self.stack:
            self.stack[-1].append(tag_obj)
        else:
            self.root_elements.append(tag_obj)

    def handle_data(self, data: str) -> None:
        """Handle text content."""
        if self.stack:
            self.stack[-1].append(data)
        else:
            self.root_elements.append(data)

    def handle_decl(self, decl: str) -> None:
        self.doctype = f"<!{decl}>"

    def get_result(self) -> Tag | Fragment | Page:
        filtered_roots = [elem for elem in self.root_elements if not (isinstance(elem, str) and not elem.strip())]

        if len(filtered_roots) == 0:
            return Fragment()
        elif len(filtered_roots) == 1:
            result = filtered_roots[0]
            if isinstance(result, str):
                return Fragment(result)

            if isinstance(result, Tag) and result.name == "html":
                head_element = None
                body_element = None

                for child in result.children:
                    if isinstance(child, Tag):
                        if child.name == "head":
                            head_element = child
                        elif child.name == "body":
                            body_element = child

                head_tags: list[Tag] = []
                if head_element:
                    for child in head_element.children:
                        if isinstance(child, Tag):
                            head_tags.append(child)

                html_attrs: dict[str, str] = {}
                for key, value in result.attributes.items():
                    if isinstance(value, str):
                        html_attrs[key] = value

                page = Page(body_element=body_element, head_elements=head_tags, **html_attrs)

                if self.doctype:
                    page.PREAMBLE = self.doctype + "\n"

                return page

            return result
        else:
            return Fragment(*filtered_roots)


def parse(html_string: str) -> Tag | Fragment | Page:
    """Parse HTML. Returns a :class:`Tag` (single root), :class:`Fragment` (multiple roots), or :class:`Page`."""
    parser = TagParser()
    parser.feed(html_string)
    parser.close()
    return parser.get_result()


def data_uri(data: bytes, media_type: str = "application/octet-stream") -> str:
    """Encode bytes as a ``data:`` URI."""
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def open_data_uri(file_path: str | Path, media_type: str | None = None) -> str:
    """Read a file and encode as a ``data:`` URI. ``media_type`` is guessed from the extension if omitted."""
    if media_type is None:
        media_type, _ = mimetypes.guess_type(file_path)
        media_type = media_type or "application/octet-stream"
    file_path = Path(file_path)
    return data_uri(file_path.read_bytes(), media_type)
