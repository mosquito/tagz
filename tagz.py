import base64
import mimetypes
from copy import copy
from dataclasses import dataclass
from functools import lru_cache
from html import escape
from pathlib import Path
from itertools import chain
from textwrap import indent
from types import MappingProxyType
from typing import (
    Any,
    Dict,
    Iterable,
    Iterator,
    List,
    Mapping,
    MutableMapping,
    MutableSet,
    Optional,
    Tuple,
    Type,
    Union,
    Callable,
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
    attributes: MutableMapping[
        str, Union[str, None, Style, Callable[[], Union[str, None, Style]]]
    ]
    _void: bool

    def __init__(
        self,
        _tag_name: str,
        *_children: Union[str, "Tag", Callable[[], Union["Tag", str]]],
        classes: Iterable[str] = (),
        _void: bool = False,
        **attributes: Union[str, None, Style, Callable[[], Union[str, None, Style]]],
    ):
        attrs: MutableMapping[
            str, Union[str, None, Style, Callable[[], Union[str, None, Style]]]
        ] = {}
        for key, value in sorted(attributes.items(), key=lambda item: item[0]):
            attrs[key.replace("_", "-")] = value

        self.name = escape(_tag_name)
        self.classes = set(classes)
        self.attributes = attrs
        self._void = _void
        if _void and _children:
            raise ValueError("Void elements cannot have children.")

        self.children = list(_children)

    def append(self, other: Union["Tag", str, Callable[[], Union["Tag", str]]]) -> None:
        if self._void:
            raise ValueError("Cannot append children to a void element.")
        return self.children.append(other)

    def __setitem__(
        self,
        key: str,
        value: Union[str, None, Style, Callable[[], Union[str, None, Style]]],
    ) -> None:
        self.attributes[escape(key)] = value

    def __getitem__(
        self, item: str
    ) -> Union[str, None, Style, Callable[[], Union[str, None, Style]]]:
        return self.attributes[escape(item)]

    def _format_attributes(self) -> str:
        parts = []
        for key, value in self.attributes.items():
            key = escape(key)
            v = value() if callable(value) else value
            if v is None:
                parts.append(key)
                continue
            v = escape(str(v), quote=True)
            parts.append(f'{key}="{v}"')
        return " ".join(parts)

    def _format_classes(self) -> str:
        if not self.classes:
            return ""
        return f'class="{" ".join(map(escape, sorted(self.classes)))}"'

    def __make_parts(self) -> Iterator[str]:
        yield self.name
        classes = self._format_classes()

        if classes:
            yield classes

        attributes = self._format_attributes()
        if attributes:
            yield attributes

    def __repr__(self) -> str:
        if not self._void:
            return f"<{' '.join(self.__make_parts())}>{'...' if self.children else ''}</{self.name}>"
        else:
            return f"<{' '.join(self.__make_parts())}/>"

    def __str__(self) -> str:
        return self.to_string()

    def _to_string(self) -> List[str]:
        parts = [f"<{' '.join(self.__make_parts())}"]
        if self._void:
            parts.append(f"/>")
            return parts

        parts.append(">")
        for child in self.children:
            value = child() if callable(child) else child
            if isinstance(value, Tag):
                parts.extend(value._to_string())
            else:
                parts.append(str(value).strip())
        parts.append(f"</{self.name}>")
        return parts

    def _to_pretty_string(self, _indent: str = "") -> List[str]:
        parts = [f"<{' '.join(self.__make_parts())}"]
        if self._void:
            parts.append(f"/>\n")
            return [indent("".join(parts), _indent)]
        
        parts.append(">\n")
        for child in self.children:
            value = child() if callable(child) else child
            if isinstance(value, Tag):
                parts.extend(value._to_pretty_string("\t"))
            else:
                child_str = str(value).strip()
                if not child_str:
                    continue
                parts.append(indent(child_str, _indent if _indent else "\t"))
                parts.append(f"\n")
        parts.append(f"</{self.name}>\n")
        return [indent("".join(parts), _indent)]

    def to_string(self, pretty: bool = False) -> str:
        return "".join(self._to_pretty_string() if pretty else self._to_string())


class TagInstance(Tag):
    __tag_name__: str
    __void__: bool = False
    __default_children__: Iterable[Union[str, Tag]] = ()
    __default_attributes__: Optional[Mapping[str, str]] = None

    def __init__(
        self,
        *_children: Union[str, "Tag", Callable[[], Union["Tag", str]]],
        classes: Iterable[str] = (),
        **attributes: Union[str, None, Style, Callable[[], Union[str, None, Style]]],
    ):
        attrs: Dict[
            str, Union[str, None, Style, Callable[[], Union[str, None, Style]]]
        ] = dict(self.__default_attributes__ or {})
        attrs.update(**attributes)
        _children = tuple(
            copy(item) for item in chain(self.__default_children__, _children)
        )

        super().__init__(self.__tag_name__, *_children, _void=self.__void__, classes=classes, **attrs)

    def __copy__(self) -> "TagInstance":
        children = tuple(copy(item) for item in self.children)
        return self.__class__(*children, classes=copy(self.classes), **self.attributes)


@lru_cache(None)
def create_tag_class(tag_name: str, **defaults: Any) -> Type[TagInstance]:
    class_attrs = {"__tag_name__": tag_name}
    if defaults:
        class_attrs.update(defaults)
    return type(
        f"Tag{tag_name.title().replace('-', '')}",
        (TagInstance,),
        class_attrs,
    )


class HTML:
    def __init__(self, defaults: Mapping[str, Mapping[str, Any]]):
        self.__defaults: Mapping[str, Mapping[str, Any]] = MappingProxyType(defaults)

    def __getitem__(self, tag_name: str) -> Type[TagInstance]:
        tag_name = tag_name.lower().replace("_", "-")
        return create_tag_class(tag_name, **self.__defaults.get(tag_name, {}))

    def __getattr__(self, tag_name: str) -> Type[TagInstance]:
        return self[tag_name.replace("_", "-")]

_void = MappingProxyType({"__void__": True})

html = HTML(
    {
        # Void elements
        "area": _void,
        "base": _void,
        "br": _void,
        "col": _void,
        "embed": _void,
        "hr": _void,
        "img": _void,
        "input": _void,
        "link": _void,
        "meta": _void,
        "param": _void,
        "source": _void,
        "track": _void,
        "wbr": _void,
    }
)


class Page:
    PREAMBLE: str = "<!doctype html>\n"

    def __init__(
        self,
        body_element: Optional[Tag] = None,
        head_elements: Iterable[Tag] = (),
        *args: Union[str, "Tag"],
        **kwargs: str,
    ):
        self.body = body_element or html.body()
        self.head = html.head(*head_elements)
        self.html = html.html(self.head, self.body, *args, **kwargs)

    def to_html5(self, pretty: bool = False) -> str:
        return "".join((self.PREAMBLE, self.html.to_string(pretty=pretty)))


def data_uri(data: bytes, media_type: str = "application/octet-stream") -> str:
    """
    Encode binary data as a data URI for use in HTML attributes.

    Args:
        data: The binary data to encode.
        media_type: The media type (MIME type) of the data. Default is 'application/octet-stream'.

    Returns:
        A string suitable for use as a data URI in an HTML attribute value.
    """

    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def open_data_uri(file_path: Union[str, Path], media_type: Optional[str] = None) -> str:
    """
    Open a file and encode its contents as a data URI for use in HTML attributes.

    Args:
        file_path: The path to the file to open.
        media_type: The media type (MIME type) of the data. If None, the type will be guessed based on the file extension.

    Returns:
        A string suitable for use as a data URI in an HTML attribute value.
    """
    if media_type is None:
        media_type, _ = mimetypes.guess_type(file_path)
        media_type = media_type or "application/octet-stream"
    file_path = Path(file_path)
    return data_uri(file_path.read_bytes(), media_type)


__all__ = (
    "HTML",
    "Page",
    "Style",
    "StyleSheet",
    "Tag",
    "TagInstance",
    "html",
    "data_uri",
    "open_data_uri",
)
