# Convert a CSV to an HTML table

**Problem.** You have CSV data — from a file, an upload, or an API —
and want it on a page as a styled table.

**Solution.** Iterate rows, wrap the first row in `<th>` tags and
the rest in `<td>`, and stream the result.

<!-- name: test_csv_to_html_table -->
```python
import csv
from io import StringIO
from tagz import html, Page, Style

source = StringIO(
    "id,name,country\n"
    "1,Ada,UK\n"
    "2,Grace,USA\n"
    "3,Linus,FI\n"
)

reader = csv.reader(source)
rows = list(reader)

table = html.table(
    border="1",
    style=Style(border_collapse="collapse"),
)
table.append(html.tr(*map(html.th, rows[0])))
for row in rows[1:]:
    table.append(html.tr(*map(html.td, row)))

page = Page(
    body_element=html.body(html.h1("People"), table),
    head_elements=(html.title("People"),),
)

out = page.to_html5()
assert "<th>id</th><th>name</th><th>country</th>" in out
assert "<td>Ada</td>" in out
assert 'style="border-collapse: collapse;"' in out
```

## Stream the file

For multi-megabyte CSVs, avoid materialising every row before
rendering. Build the table tag lazily and stream the output:

<!-- name: test_csv_streamed -->
```python
import csv
from io import StringIO
from tagz import html, Style

def render_table(reader):
    rows = iter(reader)
    head = next(rows)
    table = html.table(
        html.tr(*map(html.th, head)),
        border="1",
        style=Style(border_collapse="collapse"),
    )
    for row in rows:
        table.append(html.tr(*map(html.td, row)))
    return table

reader = csv.reader(StringIO("a,b\n1,2\n3,4\n"))
chunks = list(render_table(reader).iter_chunk(chunk_size=64))
assert "".join(chunks).startswith("<table")
assert "<th>a</th>" in "".join(chunks)
```

(You can replace `iter_chunk` with `iter_lines` for log-friendly
output.)
