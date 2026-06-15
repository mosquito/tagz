# Installation

`tagz` is a single-file pure-Python module published on PyPI.

## Requirements

- Python 3.10, 3.11, 3.12, 3.13, or 3.14
- No runtime dependencies

## Install

```bash
pip install tagz
```

With [uv](https://docs.astral.sh/uv/):

```bash
uv add tagz
```

## Add to your own `pyproject.toml`

```toml
[project]
dependencies = ["tagz>=0.7"]
```

## Verify the install

<!-- name: test_installation_smoke -->
```python
import tagz

assert hasattr(tagz, "html")
assert hasattr(tagz, "Page")
assert hasattr(tagz, "parse")
```

## What you get

`tagz` exports the following from its top-level module — see the
[API reference](api.md) for the full signatures:

- `html` — the tag factory (`html.div`, `html["my-tag"]`, …)
- `Tag`, `TagInstance` — the underlying element classes
- `Fragment`, `Raw` — wrapper-less and unescaped containers
- `Page` — full-document helper with DOCTYPE and `<html>`/`<head>`/`<body>`
- `parse` — HTML-string-to-`Tag` parser
- `Style`, `StyleSheet` — CSS helpers
- `data_uri`, `open_data_uri` — base64 encoding for `data:` URIs
- `ABSENT` — sentinel for conditionally removing an attribute
- `HTML`, `TagParser` — lower-level building blocks
