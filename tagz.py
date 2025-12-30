from copy import copy
from dataclasses import dataclass
from functools import lru_cache
from html import escape
from itertools import chain
from textwrap import indent
from types import MappingProxyType
from typing import (
    Any, Dict, Iterable, Iterator, List, Mapping, MutableMapping, MutableSet,
    Optional, Tuple, Type, Union, Callable,
)


class Style(Dict[str, Any]):
    def __init__(self, *args: Any, **kwargs: Any):
        kwargs = {key.replace("_", "-"): value for key, value in kwargs.items()}
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        return " ".join(f"{key}: {value};" for key, value in sorted(self.items()))


class StyleSheet(Dict[Union[str, Tuple[str, ...]], Style]):
    def __str__(self) -> str:
        styles = []
        for key, value in sorted(self.items(), key=str):
            if isinstance(key, tuple):
                key = ", ".join(key)
            styles.append(f"{key} {{{value}}}")
        return "\n".join(styles)


@dataclass(frozen=False)
class Tag:
    name: str
    classes: MutableSet[str]
    children: List[Union["Tag", str, Callable[[], Union["Tag", str]]]]
    attributes: MutableMapping[str, Union[str, None, Style]]

    def __init__(
        self,
        _tag_name: str,
        *_children: Union[str, "Tag", Callable[[], Union["Tag", str]]],
        classes: Iterable[str] = (),
        **attributes: Union[str, None, Style]
    ):
        attrs: MutableMapping[str, Union[str, None, Style]] = {}
        for key, value in attributes.items():
            attrs[key.replace("_", "-")] = escape(str(value))

        self.name = escape(_tag_name)
        self.classes = set(classes)
        self.attributes = attrs
        self.children = list(_children)

    def append(self, other: Union["Tag", str, Callable[[], Union["Tag", str]]]) -> None:
        return self.children.append(other)

    def __setitem__(self, key: str, value: Optional[str]) -> None:
        self.attributes[escape(key)] = escape(value) if value is not None else None

    def __getitem__(self, item: str) -> Union[str, None, Style]:
        return self.attributes[escape(item)]

    def _format_attributes(self) -> str:
        parts = []
        for key, value in self.attributes.items():
            key = escape(key)
            if value is None:
                parts.append(key)
                continue
            value = escape(str(value), quote=True)
            parts.append(f"{key}=\"{value}\"")
        return " ".join(parts)

    def _format_classes(self) -> str:
        if not self.classes:
            return ""
        return f"class=\"{' '.join(map(escape, sorted(self.classes)))}\""

    def __make_parts(self) -> Iterator[str]:
        yield self.name
        classes = self._format_classes()

        if classes:
            yield classes

        attributes = self._format_attributes()
        if attributes:
            yield attributes

    def __repr__(self) -> str:
        if self.children:
            return f"<{' '.join(self.__make_parts())}>...</{self.name}>"
        else:
            return f"<{' '.join(self.__make_parts())}/>"

    def __str__(self) -> str:
        return self.to_string()

    def _to_string(self) -> List[str]:
        parts = [f"<{' '.join(self.__make_parts())}"]
        if self.children:
            parts.append(">")
            for child in self.children:
                value = child
                # Single recursive evaluation for callables
                if callable(value):
                    value = value()
                if isinstance(value, Tag):
                    parts.extend(value._to_string())
                else:
                    parts.append(value)
            parts.append(f"</{self.name}>")
        else:
            parts.append(f"/>")
        return parts

    def _to_pretty_string(self, _indent: str = "") -> List[str]:
        parts = [f"<{' '.join(self.__make_parts())}"]
        if self.children:
            parts.append(">\n")
            for child in self.children:
                value = child
                if callable(value):
                    value = value()
                if isinstance(value, Tag):
                    parts.extend(value._to_pretty_string("\t"))
                else:
                    child_str = str(value).strip()
                    if not child_str:
                        continue
                    parts.append(indent(child_str, _indent if _indent else "\t"))
                    parts.append(f"\n")
            parts.append(f"</{self.name}>\n")
        else:
            parts.append(f"/>\n")
        return [indent("".join(parts), _indent)]

    def to_string(self, pretty: bool = False) -> str:
        return "".join(self._to_pretty_string() if pretty else self._to_string())


class TagInstance(Tag):
    __tag_name__: str
    __default_children__: Iterable[Union[str, Tag]] = ()
    __default_attributes__: Optional[Mapping[str, str]] = None

    def __init__(
        self,
        *_children: Union[str, "Tag", Callable[[], Union["Tag", str]]],
        classes: Iterable[str] = (),
        **attributes: Union[str, None, Style]
    ):
        attrs: Dict[str, Union[str, None, Style]] = (
            dict(self.__default_attributes__ or {})
        )
        attrs.update(**attributes)
        _children = tuple(
            copy(item) for item in chain(self.__default_children__, _children)
        )

        super().__init__(
            self.__tag_name__,
            *_children,
            classes=classes,
            **attrs
        )

    def __copy__(self) -> "TagInstance":
        children = tuple(copy(item) for item in self.children)
        return self.__class__(
            *children,
            classes=copy(self.classes),
            **self.attributes
        )


@lru_cache(None)
def create_tag_class(tag_name: str, **defaults: Any) -> Type[TagInstance]:
    class_attrs = {"__tag_name__": tag_name}
    if defaults:
        class_attrs.update(defaults)
    return type(
        f"Tag{tag_name.title().replace('-', '')}",
        (TagInstance,), class_attrs,
    )


class HTML:
    def __init__(self, defaults: Mapping[str, Mapping[str, Any]]):
        self.__defaults: Mapping[str, Mapping[str, Any]] = MappingProxyType(defaults)

    def __getitem__(self, tag_name: str) -> Type[TagInstance]:
        tag_name = tag_name.lower().replace("_", "-")
        return create_tag_class(tag_name, **self.__defaults.get(tag_name, {}))

    def __getattr__(self, tag_name: str) -> Type[TagInstance]:
        return self[tag_name.replace("_", "-")]


html = HTML({
    # script tag requires complete definition with closing tag
    "script": {"__default_children__": ("",)},
})


class Page:
    PREAMBLE: str = "<!doctype html>\n"

    def __init__(
        self, body_element: Optional[Tag] = None,
        head_elements: Iterable[Tag] = (),
        *args: Union[str, "Tag"], **kwargs: str
    ):
        self.body = body_element or html.body()
        self.head = html.head(*head_elements)
        self.html = html.html(self.head, self.body, *args, **kwargs)

    def to_html5(self, pretty: bool = False) -> str:
        return "".join((self.PREAMBLE, self.html.to_string(pretty=pretty)))


__all__ = (
    "HTML",
    "Page",
    "Style",
    "StyleSheet",
    "Tag",
    "TagInstance",
    "html",
)
