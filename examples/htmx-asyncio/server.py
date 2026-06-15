"""Tiny aiohttp + htmx + tagz demo.

A single page whose HTML is built entirely by tagz. htmx live-swaps in
three server-rendered fragments: server time (every second), the
requesting client's IP, and live metadata for the ``tagz`` package
pulled from the PyPI JSON API.

Run from the repo root:

    uv run --with aiohttp python examples/htmx-asyncio/server.py

Then open http://127.0.0.1:8080/.
"""

from __future__ import annotations

from datetime import datetime, timezone

import aiohttp
from aiohttp import web

from tagz import Fragment, Page, Style, StyleSheet, html


PYPI_URL = "https://pypi.org/pypi/tagz/json"


STYLES = StyleSheet({
    "*": Style(box_sizing="border-box"),
    "body": Style(
        margin="0",
        padding="2rem",
        font_family="system-ui, -apple-system, sans-serif",
        background="#f5f5f7",
        color="#1d1d1f",
        line_height="1.5",
    ),
    "h1": Style(margin="0 0 0.25rem", font_size="1.75rem"),
    ".lede": Style(color="#6e6e73", margin="0 0 2rem"),
    ".grid": Style(
        display="grid",
        gap="1rem",
        grid_template_columns="repeat(auto-fit, minmax(280px, 1fr))",
    ),
    ".card": Style(
        background="white",
        border_radius="0.75rem",
        padding="1.25rem",
        box_shadow="0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
    ),
    ".card h2": Style(
        margin="0 0 0.75rem",
        font_size="0.75rem",
        text_transform="uppercase",
        letter_spacing="0.06em",
        color="#86868b",
    ),
    ".value": Style(
        font_size="1.25rem",
        font_family="ui-monospace, SFMono-Regular, Menlo, monospace",
        word_break="break-word",
    ),
    "a": Style(color="#0066cc", text_decoration="none"),
    "a:hover": Style(text_decoration="underline"),
    "ul": Style(margin="0.75rem 0 0", padding_left="1.25rem"),
    "button": Style(
        background="#0066cc",
        color="white",
        border="0",
        padding="0.4rem 0.9rem",
        border_radius="0.4rem",
        cursor="pointer",
        font="inherit",
        margin_top="0.75rem",
    ),
    "code": Style(
        background="#f0f0f3",
        padding="0.1em 0.35em",
        border_radius="0.25rem",
        font_family="ui-monospace, SFMono-Regular, Menlo, monospace",
    ),
    "footer": Style(
        margin_top="2rem",
        color="#86868b",
        font_size="0.875rem",
    ),
})


def render_index() -> str:
    """The static landing page; htmx fills in the rest."""
    page = Page(
        lang="en",
        head_elements=(
            html.meta(charset="utf-8"),
            html.meta(name="viewport", content="width=device-width, initial-scale=1"),
            html.title("tagz + htmx demo"),
            html.script(src="https://unpkg.com/htmx.org@2.0.3"),
            html.style(STYLES),
        ),
        body_element=html.body(
            html.h1("tagz + htmx demo"),
            html.p(
                "Every byte of HTML on this page is built by tagz. "
                "htmx fetches and swaps in the live fragments below.",
                classes=["lede"],
            ),
            html.div(
                html.div(
                    html.h2("Server time (UTC)"),
                    html.div(
                        "loading…",
                        hx_get="/now",
                        hx_trigger="load, every 1s",
                        hx_swap="innerHTML",
                        classes=["value"],
                    ),
                    classes=["card"],
                ),
                html.div(
                    html.h2("Your IP"),
                    html.div(
                        "loading…",
                        id="ip-value",
                        hx_get="/ip",
                        hx_trigger="load",
                        hx_swap="innerHTML",
                        classes=["value"],
                    ),
                    html.button(
                        "Refresh",
                        hx_get="/ip",
                        hx_target="#ip-value",
                        hx_swap="innerHTML",
                    ),
                    classes=["card"],
                ),
                html.div(
                    html.h2("tagz on PyPI"),
                    html.div(
                        "loading…",
                        id="pypi-value",
                        hx_get="/pypi",
                        hx_trigger="load",
                        hx_swap="innerHTML",
                    ),
                    html.button(
                        "Refresh",
                        hx_get="/pypi",
                        hx_target="#pypi-value",
                        hx_swap="innerHTML",
                    ),
                    classes=["card"],
                ),
                classes=["grid"],
            ),
            html.footer(
                "Source: ",
                html.a(
                    "examples/htmx-asyncio",
                    href="https://github.com/mosquito/tagz/tree/master/examples/htmx-asyncio",
                ),
            ),
        ),
    )
    return page.to_html5()


def render_now() -> str:
    """Current UTC time as a wrapper-less HTML fragment."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return str(Fragment(now))


def render_ip(request: web.Request) -> str:
    """Client IP, preferring X-Forwarded-For if a proxy set it."""
    fwd = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    addr = fwd or (request.remote or "unknown")
    return str(Fragment(addr))


async def render_pypi(session: aiohttp.ClientSession) -> str:
    """Fetch the tagz JSON manifest from PyPI and render it as HTML.

    Demonstrates the recommended async pattern: await the data first,
    then build the tree from plain values.
    """
    try:
        async with session.get(
            PYPI_URL,
            timeout=aiohttp.ClientTimeout(total=5),
        ) as resp:
            resp.raise_for_status()
            payload = await resp.json()
    except Exception as exc:
        return str(Fragment(html.p(f"PyPI lookup failed: {exc}")))

    info = payload["info"]
    project_urls = info.get("project_urls") or {}

    body = Fragment(
        html.div(
            "version ",
            html.code(info["version"]),
            classes=["value"],
        ),
        html.p(info.get("summary") or ""),
        html.p(html.strong("Author: "), info.get("author") or "—"),
        html.p(html.strong("Requires Python: "), info.get("requires_python") or "—"),
        html.ul(*(
            html.li(html.a(name, href=url, target="_blank", rel="noopener"))
            for name, url in project_urls.items()
        )) if project_urls else "",
    )
    return str(body)


async def index_handler(request: web.Request) -> web.Response:
    return web.Response(text=render_index(), content_type="text/html")


async def now_handler(request: web.Request) -> web.Response:
    return web.Response(text=render_now(), content_type="text/html")


async def ip_handler(request: web.Request) -> web.Response:
    return web.Response(text=render_ip(request), content_type="text/html")


async def pypi_handler(request: web.Request) -> web.Response:
    session: aiohttp.ClientSession = request.app["http"]
    return web.Response(text=await render_pypi(session), content_type="text/html")


async def on_startup(app: web.Application) -> None:
    app["http"] = aiohttp.ClientSession()


async def on_cleanup(app: web.Application) -> None:
    await app["http"].close()


def make_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_get("/now", now_handler)
    app.router.add_get("/ip", ip_handler)
    app.router.add_get("/pypi", pypi_handler)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app


if __name__ == "__main__":
    web.run_app(make_app(), host="127.0.0.1", port=8080)
