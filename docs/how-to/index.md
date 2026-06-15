# How-to guides

Short, focused recipes. Each guide solves one problem and assumes you
already know the basics — start with the
[Tutorials](../tutorials/index.md) if you don't.

```{toctree}
:maxdepth: 1

assemble-page-in-parts
stream-to-socket
csv-to-html-table
embed-binary-with-data-uri
lazy-children-with-callables
conditional-attributes-with-absent
boolean-attributes
custom-tags
fragments-vs-raw
inline-and-embedded-css
unescaped-script-style
prefetch-async-data
htmx-with-aiohttp
```

## Recipe index

### Building pages

- [Assemble a page in parts](assemble-page-in-parts.md) — share
  references to nodes and fill them in later.
- [Custom tags](custom-tags.md) — emit non-standard tag names without
  subclassing.
- [Fragments vs Raw](fragments-vs-raw.md) — group children with no
  wrapper, or embed pre-rendered HTML safely.

### Attributes

- [Conditional attributes with `ABSENT`](conditional-attributes-with-absent.md)
- [Boolean attributes](boolean-attributes.md)
- [Inline and embedded CSS](inline-and-embedded-css.md)

### Dynamic content

- [Lazy children with callables](lazy-children-with-callables.md)
- [Pre-resolve async data](prefetch-async-data.md)
- [Unescaped content in `<script>` and `<style>`](unescaped-script-style.md)

### I/O & streaming

- [Stream HTML to a socket](stream-to-socket.md)
- [Convert a CSV file to an HTML table](csv-to-html-table.md)
- [Embed binary data with a `data:` URI](embed-binary-with-data-uri.md)

### Frameworks

- [Serve HTML fragments to htmx](htmx-with-aiohttp.md) — minimal
  aiohttp + htmx demo; a fuller version lives in
  [`examples/htmx-asyncio`](https://github.com/mosquito/tagz/tree/master/examples/htmx-asyncio).
