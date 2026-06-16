# API reference

Generated from docstrings and type-hints. The order matches the source
so related classes stay together.

## `tagz` (sync)

```{eval-rst}
.. automodule:: tagz
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource
```

## `tagz.aio` (async)

Mirror of `tagz` with async render methods. See
[Async and `tagz`](../explanation/async-and-tagz.md).

Shared value types (`Style`, `StyleSheet`, `ABSENT`, `AbsentAttribute`)
and sync-only helpers (`parse`, `TagParser`, `data_uri`, `open_data_uri`)
are re-exported as-is — see the `tagz` section above for their docs.

```{eval-rst}
.. automodule:: tagz.aio
   :members:
   :inherited-members:
   :show-inheritance:
   :member-order: bysource
   :exclude-members: Style, StyleSheet, ABSENT, AbsentAttribute, TagParser, parse, data_uri, open_data_uri
```
