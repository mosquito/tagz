import base64
import mimetypes
from copy import copy
from dataclasses import dataclass
from functools import lru_cache
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from itertools import chain
from types import MappingProxyType
from typing import (
    Any,
    AbstractSet,
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

# Cache HTML escape for performance with repeated strings
escape = lru_cache(maxsize=512)(escape)


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


class AbsentAttribute:
    pass


ABSENT = AbsentAttribute()

ChildType = Union["Tag", str, Callable[[], Union["Tag", str]]]
AttributeType = Union[
    str, None, Style, Callable[[], Union[str, None, Style, AbsentAttribute]]
]


@dataclass(frozen=False, slots=True)
class Tag:
    name: str
    children: List[ChildType]
    attributes: MutableMapping[str, AttributeType]
    _classes: MutableSet[str]
    _void: bool
    _escaped: bool

    def __init__(
        self,
        _tag_name: str,
        *_children: ChildType,
        # class is a keyword in Python, so we use 'classes' instead here, but map it to 'class' attribute
        classes: Union[Iterable[str], AbstractSet[str], str] = (),
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

        self.classes = classes  # type: ignore

    @property
    def classes(self) -> AbstractSet[str]:
        return self._classes

    @classes.setter
    def classes(self, value: Union[Iterable[str], AbstractSet[str], str]) -> None:
        # Accepts list, set, tuple, or str
        if isinstance(value, (list, set, tuple)):
            self._classes = set(escape(v, quote=True) for v in value)
            return
        elif isinstance(value, str):
            self._classes = set(escape(v, quote=True) for v in value.split())
            return

        raise TypeError(
            "Classes must be an iterable of strings or a space-separated string."
        )

    def append(self, other: ChildType) -> None:
        if self._void:
            raise ValueError("Cannot append children to a void element.")

        if isinstance(other, str) and self._escaped:
            other = escape(other)
        return self.children.append(other)

    def __setitem__(self, key: str, value: AttributeType) -> None:
        k = escape(key)

        if k in ("class", "classes"):
            # Map 'class' and 'classes' attributes to the classes property
            self.classes = value  # type: ignore
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

    def _format_attributes(self) -> str:
        parts = []
        # Sort attributes for deterministic output
        for key, value in sorted(self.attributes.items()):
            key = escape(key)
            v = value() if callable(value) else value
            if v is ABSENT:
                continue
            if v is None:
                parts.append(key)
                continue
            v = escape(str(v), quote=True)
            parts.append(f'{key}="{v}"')
        return " ".join(parts)

    def _format_classes(self) -> str:
        if not self.classes:
            return ""
        return f'class="{" ".join(sorted(self.classes))}"'

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
            parts.append("".join(self._format_tag_close()))
            return "".join(parts)

        parts.append(f"{'...' if self.children else ''}")
        parts.append(f"</{self.name}>")
        return "".join(parts)

    def __str__(self) -> str:
        return self.to_string()

    def _to_string(self, indent: str = "", indent_str: str = "") -> Iterable[str]:
        yield indent
        yield from self._format_tag_open()

        if indent_str:
            yield "\n"

        if self._void:
            yield from self._format_tag_close()
            return

        for child in self.children:
            if callable(child):
                child = child()
                if isinstance(child, str) and self._escaped:
                    child = escape(child)

            if isinstance(child, Tag):
                yield from child._to_string(indent + indent_str, indent_str)
            else:
                child_str = str(child)
                if not child_str:
                    # Only output non-empty strings
                    continue

                if indent_str and "\n" in child_str:
                    # Handle multi-line strings in pretty mode
                    lines = child_str.split("\n")
                    for line in lines:
                        yield indent
                        yield indent_str
                        yield line
                        yield "\n"
                    continue

                yield indent
                yield indent_str
                yield child_str
                if indent_str:
                    yield "\n"
        yield indent
        yield from self._format_tag_close()
        if indent_str:
            yield "\n"

    def iter_string(self, pretty: bool = False) -> Iterator[str]:
        yield from self._to_string("", "\t" if pretty else "")

    def iter_lines(self, indent_char: str = "\t") -> Iterator[str]:
        """
        Iterate over the pretty-printed HTML output line by line.

        This method always formats with indentation and yields complete lines
        without trailing newlines. Useful for streaming HTML output line by line
        to files or network sockets.

        Args:
            indent_char: The character(s) to use for indentation. Defaults to tab.

        Yields:
            Lines of HTML without trailing newlines.

        Example:
            >>> tag = html.div(html.p("Hello"), html.p("World"))
            >>> for line in tag.iter_lines():
            ...     print(line)
            <div>
                <p>
                    Hello
                </p>
                <p>
                    World
                </p>
            </div>
        """
        accu = ""
        for chunk in self._to_string("", indent_char):
            if "\n" in chunk:
                parts = chunk.split("\n")
                # Yield all complete lines (everything before the last part)
                for part in parts[:-1]:
                    yield accu + part
                    accu = ""
                # Keep the remainder for the next line
                accu = parts[-1]
            else:
                accu += chunk

        # Yield any remaining content
        if accu:
            yield accu

    def iter_chunk(
        self, chunk_size: int = 4096, pretty: bool = False, indent_char: str = "\t"
    ) -> Iterator[str]:
        """
        Iterate over the HTML output in fixed-size chunks.

        This method accumulates HTML output and yields chunks of approximately
        the specified size. Useful for streaming large HTML documents over
        network connections or writing to buffered outputs with specific
        buffer sizes.

        Args:
            chunk_size: Target size for each chunk in bytes. Defaults to 4096.
                       The actual chunk size may be slightly larger to avoid
                       breaking in the middle of a fragment.
            pretty: If True, format with indentation and newlines.
            indent_char: The character(s) to use for indentation when pretty=True.
                        Defaults to tab character.

        Yields:
            Chunks of HTML as strings, each approximately chunk_size bytes.

        Example:
            >>> tag = html.div(html.p("Hello") * 1000)
            >>> for chunk in tag.iter_chunk(chunk_size=1024):
            ...     socket.send(chunk.encode())
        """
        buffer = ""
        for fragment in self._to_string("", indent_char if pretty else ""):
            buffer += fragment
            # Yield chunks when buffer exceeds chunk_size
            while len(buffer) >= chunk_size:
                yield buffer[:chunk_size]
                buffer = buffer[chunk_size:]

        # Yield any remaining content
        if buffer:
            yield buffer

    def to_string(self, pretty: bool = False) -> str:
        return "".join(self.iter_string(pretty=pretty))


class TagInstance(Tag):
    __tag_name__: str
    __void__: bool = False
    __escaped__: bool = True
    __default_children__: Iterable[Union[str, Tag]] = ()
    __default_attributes__: Optional[Mapping[str, str]] = None

    def __init__(
        self,
        *_children: ChildType,
        classes: Iterable[str] = (),
        **attributes: AttributeType,
    ):
        attrs: Dict[str, AttributeType] = dict(self.__default_attributes__ or {})
        attrs.update(**attributes)
        # Optimize: avoid chain() overhead if no default children
        children_iter = (
            chain(self.__default_children__, _children)
            if self.__default_children__
            else _children
        )
        _children = tuple(
            # No need to copy strings
            item if isinstance(item, str) else copy(item)
            for item in children_iter
        )

        super().__init__(
            self.__tag_name__,
            *_children,
            _void=self.__void__,
            _escaped=self.__escaped__,
            classes=classes,
            **attrs,
        )

    def __copy__(self) -> "TagInstance":
        children = tuple(
            item if isinstance(item, str) else copy(item) for item in self.children
        )
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


class Fragment(Tag):
    """
    A Fragment necessary to group children without adding extra tags.
    Each child maintains its own escaping behavior.
    """

    def __init__(self, *_children: ChildType, _escaped: bool = True):
        super().__init__("", *_children, _escaped=_escaped)

    def _format_tag_open(self) -> Iterator[str]:
        yield ""

    def _format_tag_close(self) -> Iterator[str]:
        yield ""

    def _to_string(self, indent: str = "", indent_str: str = "") -> Iterable[str]:
        return super()._to_string("", "")


class Raw(Fragment):
    """
    A Tag that renders raw, unwrapped content.
    It is completely unescaped and really unsafe against XSS.
    The best practice is to avoid using this unless absolutely necessary.
    """

    def __init__(self, content: str):
        super().__init__("", content, _escaped=False)


_void = MappingProxyType({"__void__": True})
_unescaped = MappingProxyType({"__escaped__": False})

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
        # Unescaped content
        "script": _unescaped,
        "style": _unescaped,
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


class TagParser(HTMLParser):
    """HTML parser that builds Tag objects from HTML strings."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root_elements: List[Union[Tag, str]] = []
        self.stack: List[Tag] = []
        self.doctype: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        """Handle opening tag."""
        # Convert attrs list to dict, handling class specially
        tag_attrs: Dict[str, Any] = {}
        classes: List[str] = []

        for key, value in attrs:
            if key == "class":
                classes.extend(value.split() if value else [])
            else:
                tag_attrs[key] = value if value is not None else None

        # Create tag instance
        tag_obj = html[tag](**tag_attrs)
        if classes:
            tag_obj.classes = set(classes)

        # Add to parent or root
        if self.stack:
            self.stack[-1].append(tag_obj)
        else:
            self.root_elements.append(tag_obj)

        # Push to stack (will be popped on endtag)
        self.stack.append(tag_obj)

    def handle_endtag(self, tag: str) -> None:
        """Handle closing tag."""
        if self.stack:
            self.stack.pop()

    def handle_startendtag(
        self, tag: str, attrs: List[Tuple[str, Optional[str]]]
    ) -> None:
        """Handle self-closing/void tag."""
        tag_attrs: Dict[str, Any] = {}
        classes: List[str] = []

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
            # Text at root level
            self.root_elements.append(data)

    def handle_decl(self, decl: str) -> None:
        """Handle DOCTYPE declaration."""
        self.doctype = f"<!{decl}>"

    def get_result(self) -> Union[Tag, Fragment, Page]:
        """Get the parsed result."""
        # Filter out whitespace-only text nodes at root level
        filtered_roots = [
            elem
            for elem in self.root_elements
            if not (isinstance(elem, str) and not elem.strip())
        ]

        if len(filtered_roots) == 0:
            return Fragment()
        elif len(filtered_roots) == 1:
            result = filtered_roots[0]
            if isinstance(result, str):
                # Single text node -> wrap in Fragment
                return Fragment(result)

            # Check if it's a full HTML document
            if isinstance(result, Tag) and result.name == "html":
                # Extract head and body
                head_element = None
                body_element = None

                for child in result.children:
                    if isinstance(child, Tag):
                        if child.name == "head":
                            head_element = child
                        elif child.name == "body":
                            body_element = child

                # Extract head children that are Tag objects
                head_tags: List[Tag] = []
                if head_element:
                    for child in head_element.children:
                        if isinstance(child, Tag):
                            head_tags.append(child)

                # Filter attributes to only string values
                html_attrs: Dict[str, str] = {}
                for key, value in result.attributes.items():
                    if isinstance(value, str):
                        html_attrs[key] = value

                # Create Page object
                page = Page(
                    body_element=body_element, head_elements=head_tags, **html_attrs
                )

                # Override preamble if we have a custom DOCTYPE
                if self.doctype:
                    page.PREAMBLE = self.doctype + "\n"

                return page

            return result
        else:
            # Multiple root elements
            return Fragment(*filtered_roots)


def parse(html_string: str) -> Union[Tag, Fragment, Page]:
    """
    Parse HTML string into Tag objects.

    Args:
        html_string: The HTML string to parse.

    Returns:
        A Tag object if there's a single root element,
        a Fragment if there are multiple root elements or text nodes,
        or a Page if the HTML contains a complete document with <html> tag.

    Example:
        >>> tag = parse('<div class="container"><p>Hello</p></div>')
        >>> print(tag)
        <div class="container"><p>Hello</p></div>

        >>> fragment = parse('<p>First</p><p>Second</p>')
        >>> print(fragment)
        <p>First</p><p>Second</p>

        >>> page = parse('<!DOCTYPE html><html><head></head><body>Content</body></html>')
        >>> isinstance(page, Page)
        True
    """
    parser = TagParser()
    parser.feed(html_string)
    parser.close()
    return parser.get_result()


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
    "ABSENT",
    "data_uri",
    "Fragment",
    "html",
    "HTML",
    "open_data_uri",
    "Page",
    "parse",
    "Raw",
    "Style",
    "StyleSheet",
    "Tag",
    "TagInstance",
    "TagParser",
)
