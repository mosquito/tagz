"""Shared pytest fixtures for cross-flavour tests.

The ``runtime`` fixture is parameterised over the sync :mod:`tagz` and async
:mod:`tagz.aio` modules. It yields ``(module, render)``: ``render(obj)``
calls ``to_html5`` if available (Page) or ``to_string`` otherwise (Tag),
and runs the coroutine through :func:`asyncio.run` for the async flavour.

    def test_x(runtime):
        tz, render = runtime
        assert render(tz.html.div("hi")) == "<div>hi</div>"
"""

from __future__ import annotations

import asyncio
from typing import Any
from collections.abc import Callable

import pytest

import tagz
from tagz import aio as tagz_async


def _pick_method(obj: Any) -> str:
    return "to_html5" if hasattr(obj, "to_html5") else "to_string"


def _render_sync(obj: Any, **kwargs: Any) -> str:
    return getattr(obj, _pick_method(obj))(**kwargs)


def _render_async(obj: Any, **kwargs: Any) -> str:
    return asyncio.run(getattr(obj, _pick_method(obj))(**kwargs))


_FLAVOURS = {
    "sync": (tagz, _render_sync),
    "async": (tagz_async, _render_async),
}


@pytest.fixture(params=list(_FLAVOURS), ids=list(_FLAVOURS))
def runtime(
    request: pytest.FixtureRequest,
) -> tuple[Any, Callable[..., str]]:
    """``(module, render)`` for the requested flavour."""
    return _FLAVOURS[request.param]
