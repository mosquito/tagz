# Embed binary data with a `data:` URI

**Problem.** You want to inline a small image, font, or other binary
asset into the HTML instead of referencing an external file.

**Solution.** Use `data_uri()` to base64-encode raw bytes, or
`open_data_uri()` to read a file from disk.

## From bytes

<!-- name: test_data_uri_bytes -->
```python
from tagz import data_uri, html

# A trivial GIF (1×1 transparent pixel).
gif_bytes = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00"
    b"!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01"
    b"\x00\x00\x02\x02D\x01\x00;"
)

src = data_uri(gif_bytes, media_type="image/gif")
img = html.img(src=src, alt="dot")

assert src.startswith("data:image/gif;base64,")
assert 'alt="dot"' in str(img)
```

## From a file path

`open_data_uri()` reads the file and guesses the media type from
the extension if you don't supply one.

<!-- name: test_data_uri_file -->
```python
from tempfile import NamedTemporaryFile
from tagz import open_data_uri, html

with NamedTemporaryFile("wb", suffix=".txt") as f:
    f.write(b"hello world")
    f.flush()
    src = open_data_uri(f.name)

assert src.startswith("data:text/plain;base64,")
```

## When to use this

- **Email templates** — many clients refuse external `<img src>`
  references for privacy. Inlined data URIs render reliably.
- **Self-contained reports** — a single `.html` file you can email
  or open offline.
- **Tiny assets** — favicons, sprites, small logos.

Avoid for large assets: base64 inflates payload by ~33%, and you
lose HTTP caching.
