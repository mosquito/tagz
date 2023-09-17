import io
from dataclasses import dataclass
from functools import lru_cache
from html import escape
from itertools import chain
from textwrap import indent
from types import MappingProxyType
from typing import Optional, Iterable, MutableSet, MutableMapping, List, Union, Mapping, Any, Type, Iterator


@dataclass(frozen=False)
class Tag:
    name: str
    classes: MutableSet[str]
    attributes: MutableMapping[str, Optional[str]]
    children: List[Union["Tag", str]]

    def __init__(
        self,
        _tag_name: str,
        *_children: Union[str, "Tag"],
        classes: Iterable[str] = (),
        **attributes: str
    ):
        attrs: MutableMapping[str, Optional[str]] = {}
        for key, value in attributes.items():
            attrs[key.replace('_', '-')] = escape(value)

        self.name = escape(_tag_name)
        self.classes = set(classes)
        self.attributes = attrs
        self.children = list(_children)

    def append(self, other: Union["Tag", str]) -> None:
        return self.children.append(other)

    def __setitem__(self, key: str, value: Optional[str]) -> None:
        self.attributes[escape(key)] = escape(value) if value is not None else None

    def __getitem__(self, item: str) -> Optional[str]:
        return self.attributes[escape(item)]

    def _format_attributes(self) -> str:
        parts = []
        for key, value in self.attributes.items():
            key = escape(key)
            if value is None:
                parts.append(key)
                continue
            value = escape(value, quote=True)
            parts.append(f"{key}=\"{value}\"")
        return " ".join(parts)

    def _format_classes(self) -> str:
        if not self.classes:
            return ''
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
        return self._to_string()

    def _to_string(self) -> str:
        with io.StringIO() as fp:
            fp.write(f"<{' '.join(self.__make_parts())}")
            if self.children:
                fp.write(f">")
                for child in self.children:
                    fp.write(str(child))
                fp.write(f"</{self.name}>")
            else:
                fp.write(f"/>")
            return fp.getvalue()

    def _to_pretty_string(self, _indent: str = "") -> str:
        with io.StringIO() as fp:
            fp.write(f"<{' '.join(self.__make_parts())}")
            if self.children:
                fp.write(f">\n")
                for child in self.children:
                    if isinstance(child, Tag):
                        fp.write(child._to_pretty_string("\t"))
                    else:
                        child_str = str(child)
                        if not child_str.strip():
                            continue
                        fp.write(indent(child_str, _indent if _indent else "\t"))
                        fp.write(f"\n")
                fp.write(f"</{self.name}>\n")
            else:
                fp.write(f"/>\n")
            return indent(fp.getvalue(), _indent)

    def to_string(self, pretty: bool = False) -> str:
        return self._to_pretty_string() if pretty else self._to_string()


class TagInstance(Tag):
    __tag_name__: str
    __default_children__: Iterable[Union[str, Tag]] = ()
    __default_attributes__: Optional[Mapping[str, str]] = None

    def __init__(
        self,
        *_children: Union[str, "Tag"],
        classes: Iterable[str] = (),
        **attributes: str
    ):
        super().__init__(
            self.__tag_name__,
            *chain(self.__default_children__, _children),
            classes=classes,
            **attributes,
            **(self.__default_attributes__ or {})
        )


@lru_cache(None)
def create_tag_class(tag_name: str, **defaults: Any) -> Type[TagInstance]:
    class_attrs = {"__tag_name__": tag_name}
    if defaults:
        class_attrs.update(defaults)
    return type(
        f"Tag{tag_name.title().replace('-', '')}",
        (TagInstance,), class_attrs
    )


class HTML:
    def __init__(self, defaults: Mapping[str, Mapping[str, Any]]):
        self.__defaults: Mapping[str, Mapping[str, Any]] = MappingProxyType(defaults)

    def __getitem__(self, tag_name: str) -> Type[TagInstance]:
        return create_tag_class(tag_name, **self.__defaults.get(tag_name, {}))

    def __getattr__(self, tag_name: str) -> Type[TagInstance]:
        return self[tag_name.replace("_", "-")]


html = HTML({
    "script": {"__default_children__": ("",)}
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
        with io.StringIO() as fp:
            fp.write(self.PREAMBLE)
            fp.write(self.html.to_string(pretty=pretty))
            return fp.getvalue()


__all__ = (
    "HTML",
    "Page",
    "Tag",
    "TagInstance",
    "html",
)
