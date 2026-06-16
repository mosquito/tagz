"""Shared core for :mod:`tagz` and :mod:`tagz.aio`: value types, type aliases, :class:`TagBase`, the
:class:`HTMLBase` factory machinery, :data:`HTML_DEFAULTS`, and :class:`PageBase`.
"""

from __future__ import annotations

from copy import copy
from dataclasses import dataclass
from functools import lru_cache
from html import escape as _escape
from types import MappingProxyType
from collections.abc import Callable, Iterable, Iterator, Mapping, MutableMapping, MutableSet, Set
from typing import Any, TypeAlias, cast


__all__ = (
    "ABSENT",
    "AbsentAttribute",
    "AttributeType",
    "ChildType",
    "HTMLBase",
    "HTML_DEFAULTS",
    "PageBase",
    "Style",
    "StyleSheet",
    "TagBase",
    "create_tag_class",
    "escape",
)


#: Cached :func:`html.escape`, memoised on ``(text, quote)`` for tight render loops.
escape = lru_cache(maxsize=512)(_escape)


class Style(dict[str, Any]):
    """CSS declaration block. Underscores in keys map to hyphens; declarations are sorted by key."""

    def __init__(self, *args: Any, **kwargs: Any):
        kwargs = {key.replace("_", "-"): value for key, value in kwargs.items()}
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return " ".join(f"{key}: {value};" for key, value in sorted(self.items()))


class StyleSheet(dict[str | tuple[str, ...], Style]):
    """Selector → :class:`Style` mapping. Tuple keys render as a comma-separated selector list."""

    def __str__(self) -> str:
        styles = []
        for key, value in sorted(self.items(), key=str):
            if isinstance(key, tuple):
                key = ", ".join(key)
            styles.append(f"{key} {{{value}}}")
        return "\n".join(styles)


class AbsentAttribute:
    """Sentinel type for :data:`ABSENT`."""


ABSENT = AbsentAttribute()
"""When used as an attribute value, removes the attribute from the rendered output."""


@dataclass(eq=False, slots=True)
class TagBase:
    """Data + internal helpers shared by sync and async tags.

    The public render API lives on the concrete :class:`tagz.Tag` (sync) and :class:`tagz.aio.Tag` (async) - keeping
    it off the base avoids a Liskov override conflict between sync and async signatures.
    """

    name: str
    children: list[ChildType]
    attributes: MutableMapping[str, AttributeType]
    _classes: MutableSet[str]
    _void: bool
    _escaped: bool

    def __init__(
        self,
        _tag_name: str,
        *_children: ChildType,
        # class is a keyword in Python, so we use 'classes' instead here, but map it to 'class' attribute
        classes: Iterable[str] | Set[str] | str = (),
        _void: bool = False,
        _escaped: bool = True,
        **attributes: AttributeType,
    ):
        self.name = escape(_tag_name)
        self._classes = set()
        self.attributes = {}
        self._void = _void
        self._escaped = _escaped

        self.children = list()
        for child in _children:
            self.append(child)

        for key, value in sorted(attributes.items(), key=lambda item: item[0]):
            self[key.replace("_", "-")] = value

        self.classes = classes

    @property
    def classes(self) -> Set[str]:
        return self._classes

    @classes.setter
    def classes(self, value: Iterable[str] | Set[str] | str) -> None:
        """Replace the class set. Accepts an iterable or a space-separated string; values are HTML-escaped."""
        if isinstance(value, (list, set, tuple)):
            self._classes = set(escape(v, quote=True) for v in value)
            return
        elif isinstance(value, str):
            self._classes = set(escape(v, quote=True) for v in value.split())
            return

        raise TypeError("Classes must be an iterable of strings or a space-separated string.")

    def append(self, other: ChildType) -> None:
        """Append a child. Strings are escaped (unless ``_escaped=False``); callables run at render time."""
        if self._void:
            raise ValueError("Cannot append children to a void element.")

        if isinstance(other, str) and self._escaped:
            other = escape(other)
        return self.children.append(other)

    def __setitem__(self, key: str, value: AttributeType) -> None:
        """``"class"``/``"classes"`` → :attr:`classes`. ``True``/``False``/``ABSENT`` toggle/strip the attribute."""
        k = escape(key)

        if k in ("class", "classes"):
            self.classes = value  # type: ignore[assignment]
            return

        if value is ABSENT:
            self.attributes.pop(k, None)
            return

        if isinstance(value, bool):
            value = None if value else ABSENT

        self.attributes[k] = value

    def __getitem__(self, item: str) -> AttributeType:
        return self.attributes[escape(item)]

    def __delitem__(self, key: str) -> None:
        del self.attributes[escape(key)]

    def _format_attribute(self, key: str, value: Any) -> str | None:
        """Render one resolved attribute. ``None`` skips it; ``value is None`` yields a boolean attribute."""
        if value is ABSENT:
            return None
        ekey = escape(key)
        if value is None:
            return ekey
        if isinstance(value, TagBase):
            value = repr(value)
        return f'{ekey}="{escape(str(value), quote=True)}"'

    def _format_classes(self) -> str:
        if not self.classes:
            return ""
        return f'class="{" ".join(sorted(self.classes))}"'

    def __repr__(self) -> str:
        if self._void:
            return f"<{self.name}/>"
        return f"<{self.name}>{'...' if self.children else ''}</{self.name}>"

    def __copy__(self) -> TagBase:
        """Shallow copy that bypasses ``__init__`` (no re-escape). TagBase children are recursively copied;
        strings, coroutines, awaitables and other leaf values are shared."""
        clone = object.__new__(self.__class__)
        clone.name = self.name
        clone.children = [copy(c) if isinstance(c, TagBase) else c for c in self.children]
        clone.attributes = dict(self.attributes)
        clone._classes = set(self._classes)
        clone._void = self._void
        clone._escaped = self._escaped
        return clone

    def _iter_leaf(self, child: Any, indent: str, indent_str: str) -> Iterator[str]:
        """Yield rendered chunks for a non-Tag child. Caller is responsible for HTML-escape upstream."""
        child_str = str(child)
        if not child_str:
            return
        if indent_str and "\n" in child_str:
            for line in child_str.split("\n"):
                yield indent
                yield indent_str
                yield line
                yield "\n"
            return
        yield indent
        yield indent_str
        yield child_str
        if indent_str:
            yield "\n"

    def _iter_children(self) -> Iterator[Any]:
        """Resolve children: invoke sync callables once; coroutines/awaitables/async iterables pass through."""
        for child in self.children:
            if callable(child):
                child = child()
                if isinstance(child, str) and self._escaped:
                    child = escape(child)
            yield child


ChildType: TypeAlias = TagBase | str | Callable[[], TagBase | str]
AttributeType: TypeAlias = str | None | Style | Callable[[], str | None | Style | AbsentAttribute]


@lru_cache(None)
def create_tag_class(base_cls: type, name_prefix: str, tag_name: str, **defaults: Any) -> type:
    """Build and cache a per-tag subclass of ``base_cls``. Cache key includes ``base_cls`` + ``name_prefix``."""
    class_attrs: dict[str, Any] = {"__tag_name__": tag_name}
    if defaults:
        class_attrs.update(defaults)
    return type(
        f"{name_prefix}{tag_name.title().replace('-', '')}",
        (base_cls,),
        class_attrs,
    )


class HTMLBase:
    """Factory machinery for sync/async :class:`HTML`. Subclasses bind :attr:`__tag_fabric__`."""

    __tag_fabric__: type[TagBase]
    _name_prefix: str = "Tag"

    def __init__(self, defaults: Mapping[str, Mapping[str, Any]]):
        self._defaults: Mapping[str, Mapping[str, Any]] = MappingProxyType(dict(defaults))

    def __getitem__(self, tag_name: str) -> type[Any]:
        tag_name = tag_name.lower().replace("_", "-")
        # cast: mypy 2.1 rejects Type[TagBase] as Hashable for dataclass(slots=True), even though it is.
        return create_tag_class(
            cast(type, self.__tag_fabric__),
            self._name_prefix,
            tag_name,
            **self._defaults.get(tag_name, {}),
        )

    def __getattr__(self, tag_name: str) -> type[Any]:
        cls = self[tag_name.replace("_", "-")]
        self.__dict__[tag_name] = cls
        return cls


_void_default = MappingProxyType({"__void__": True})
_unescaped_default = MappingProxyType({"__escaped__": False})

#: Per-tag defaults for HTML5 void and unescaped elements; shared between sync and async factories.
HTML_DEFAULTS = MappingProxyType(
    {
        # Void elements
        "area": _void_default,
        "base": _void_default,
        "br": _void_default,
        "col": _void_default,
        "embed": _void_default,
        "hr": _void_default,
        "img": _void_default,
        "input": _void_default,
        "link": _void_default,
        "meta": _void_default,
        "param": _void_default,
        "source": _void_default,
        "track": _void_default,
        "wbr": _void_default,
        # Unescaped content
        "script": _unescaped_default,
        "style": _unescaped_default,
    }
)


class PageBase:
    """``<html>``/``<head>``/``<body>`` composition shared by sync and async ``Page``.

    Concrete subclasses must define ``__html__`` (the tag factory) and ``to_html5`` (sync or async).
    """

    #: DOCTYPE emitted before ``<html>``. Override for a non-HTML5 doctype.
    PREAMBLE: str = "<!doctype html>\n"

    __html__: HTMLBase
    body: TagBase
    head: TagBase
    html: TagBase

    def __init__(
        self,
        body_element: TagBase | None = None,
        head_elements: Iterable[TagBase] = (),
        *args: str | TagBase,
        **kwargs: str,
    ):
        f = self.__html__
        self.body = body_element or f.body()
        self.head = f.head(*head_elements)
        self.html = f.html(self.head, self.body, *args, **kwargs)
