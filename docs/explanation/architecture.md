# Architecture

The class hierarchy is small on purpose. Five classes carry the
entire model.

```{mermaid}
classDiagram
    class Tag {
        +name: str
        +children: list
        +attributes: dict
        +classes: set
        +append(child)
        +to_string(pretty)
        +iter_string()
        +iter_lines()
        +iter_chunk()
    }
    class TagInstance {
        +__tag_name__
        +__void__
        +__escaped__
    }
    class Fragment {
        rendered without wrapper
    }
    class Raw {
        rendered verbatim, no escape
    }
    class Page {
        +PREAMBLE: doctype
        +head
        +body
        +html
        +to_html5(pretty)
    }
    Tag <|-- TagInstance
    Tag <|-- Fragment
    Fragment <|-- Raw
    Page o-- Tag : composes
```

## The five classes

### `Tag`

The base class. Stores a tag name, children, attributes, classes,
and two flags: ``_void`` (no closing tag, no children allowed) and
``_escaped`` (HTML-escape string children/attribute values).

You can construct a `Tag` directly, but in practice you don't —
everything routes through the :data:`html` factory.

### `TagInstance`

A `Tag` subclass with element-specific defaults baked into class
attributes (``__tag_name__``, ``__void__``, ``__escaped__``,
optionally ``__default_children__`` and ``__default_attributes__``).
Each named tag — `div`, `br`, `script`, anything you ask for — is a
dynamically created `TagInstance` subclass cached by `lru_cache` so
that `html.div` always returns the same class.

### `Fragment`

`Fragment` is a `Tag` with an empty name and overridden
``_format_tag_open`` / ``_format_tag_close`` that emit nothing. It
renders its children inline with no surrounding markup. Equivalent
to React's fragment.

### `Raw`

`Raw` is a `Fragment` that disables escaping for its single
content string. Use it when you have pre-rendered HTML you want to
splice in unmodified.

### `Page`

A small composition helper. Holds a `head` `<head>` tag, a `body`
`<body>` tag, and an `<html>` root that contains both. The
`PREAMBLE` class attribute is the DOCTYPE — override it for non-
HTML5 documents.

## How `html.div(...)` actually works

<!-- name: test_architecture_factory_mechanics -->
```python
from tagz import html, TagInstance, Tag

# `html.div` is a CLASS, not a function.
assert isinstance(html.div, type)
assert issubclass(html.div, TagInstance)
assert issubclass(html.div, Tag)

# Calling it produces an instance whose tag name comes from the
# class attribute __tag_name__.
inst = html.div("hi")
assert inst.__tag_name__ == "div"
assert inst.name == "div"

# Two attribute lookups return the same cached class.
assert html.div is html.div
```

## Why a dataclass with `slots=True`?

`Tag` uses ``@dataclass(slots=True)`` mostly for memory efficiency
in trees with many small nodes (think CSV → 10k rows × N cells).
Slots also stop accidental attribute typos from silently succeeding.

## What's not here

- **No DOM-style parent links.** Children know nothing about who
  contains them. This keeps trees cheap to copy and impossible to
  cycle.
- **No event system.** `tagz` is rendering-only.
- **No async surface in `tagz` itself.** The sync core stays dependency-
  free of `asyncio`. The async mirror lives in a separate module —
  see [Async and tagz](async-and-tagz.md).
