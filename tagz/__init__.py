"""tagz - a typed HTML builder.

Sync flavour: ``html``, ``Page``, ``Tag``, ``Fragment``, ``Raw``, ``Style``, ``StyleSheet``, ``ABSENT``,
``parse``, ``TagParser``, ``data_uri``, ``open_data_uri``.

Async streaming lives in :mod:`tagz.aio` - same symbol names, async signatures.
"""

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
from .sync import (
    HTML,
    Fragment,
    Page,
    Raw,
    Tag,
    TagInstance,
    TagParser,
    data_uri,
    html,
    open_data_uri,
    parse,
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
