"""Coverage for :func:`tagz.aio.ensure_awaitable`.

The helper accepts a callable / coroutine / awaitable and returns an
:class:`Awaitable` that resolves to the final value. It's used at
lazy-callable boundaries in the async renderer so a single ``await``
works regardless of whether the source is an async-def function, a
coroutine, a Future, or a plain sync callable.
"""

from __future__ import annotations

import asyncio
import inspect

import pytest

from tagz.aio import ensure_awaitable


# ---------------------------------------------------------------------------
# Always returns an awaitable
# ---------------------------------------------------------------------------


def test_returns_awaitable_for_async_def_function():
    async def coro():
        return "x"

    result = ensure_awaitable(coro)
    try:
        assert inspect.isawaitable(result)
    finally:
        result.close()


def test_returns_awaitable_for_coroutine_object():
    async def coro():
        return "x"

    co = coro()
    try:
        result = ensure_awaitable(co)
        assert inspect.isawaitable(result)
    finally:
        co.close()


def test_returns_awaitable_for_sync_callable():
    async def go():
        return ensure_awaitable(lambda: "hello")

    result = asyncio.run(go())
    assert inspect.isawaitable(result)


def test_returns_awaitable_for_future():
    async def go():
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        fut.set_result("hello")
        return ensure_awaitable(fut)

    result = asyncio.run(go())
    assert inspect.isawaitable(result)


# ---------------------------------------------------------------------------
# Resolution: a single await yields the final value
# ---------------------------------------------------------------------------


def test_resolves_async_def_function_to_return_value():
    async def coro():
        return "from coro"

    async def go():
        return await ensure_awaitable(coro)

    assert asyncio.run(go()) == "from coro"


def test_resolves_coroutine_object_to_return_value():
    async def coro():
        return "from coro obj"

    async def go():
        return await ensure_awaitable(coro())

    assert asyncio.run(go()) == "from coro obj"


def test_resolves_future_to_set_result():
    async def go():
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        loop.call_soon(fut.set_result, "from future")
        return await ensure_awaitable(fut)

    assert asyncio.run(go()) == "from future"


def test_resolves_task():
    async def coro():
        await asyncio.sleep(0)
        return 42

    async def go():
        task = asyncio.create_task(coro())
        return await ensure_awaitable(task)

    assert asyncio.run(go()) == 42


def test_resolves_sync_callable_via_loop_call_soon():
    calls = [0]

    def sync_fn():
        calls[0] += 1
        return "sync result"

    async def go():
        return await ensure_awaitable(sync_fn)

    assert asyncio.run(go()) == "sync result"
    assert calls[0] == 1


def test_sync_callable_with_args_via_partial():
    from functools import partial

    async def go():
        return await ensure_awaitable(partial(str.upper, "hi"))

    assert asyncio.run(go()) == "HI"


# ---------------------------------------------------------------------------
# Order of execution
# ---------------------------------------------------------------------------


def test_sync_callable_runs_when_future_is_awaited():
    """A sync callable is scheduled via ``loop.call_soon`` and runs
    once the event loop reaches the next iteration."""
    order = []

    def sync_fn():
        order.append("sync_fn")
        return "v"

    async def go():
        order.append("before")
        aw = ensure_awaitable(sync_fn)  # schedules sync_fn
        order.append("after schedule")
        # sync_fn has been scheduled but not yet run.
        assert "sync_fn" not in order
        result = await aw  # event loop tick → sync_fn runs
        order.append("done")
        return result

    assert asyncio.run(go()) == "v"
    assert order == ["before", "after schedule", "sync_fn", "done"]


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


def test_async_callable_exception_propagates():
    class Boom(Exception):
        pass

    async def coro():
        raise Boom("nope")

    async def go():
        return await ensure_awaitable(coro)

    with pytest.raises(Boom, match="nope"):
        asyncio.run(go())


def test_sync_callable_exception_propagates():
    class Boom(Exception):
        pass

    def sync_fn():
        raise Boom("nope")

    async def go():
        return await ensure_awaitable(sync_fn)

    with pytest.raises(Boom, match="nope"):
        asyncio.run(go())


def test_already_failed_future_propagates():
    class Boom(Exception):
        pass

    async def go():
        loop = asyncio.get_running_loop()
        fut = loop.create_future()
        fut.set_exception(Boom("boom"))
        return await ensure_awaitable(fut)

    with pytest.raises(Boom, match="boom"):
        asyncio.run(go())


# ---------------------------------------------------------------------------
# Re-callable inputs
# ---------------------------------------------------------------------------


def test_async_def_function_is_recallable():
    """An async-def function (not a coroutine object) can be passed twice."""

    async def coro():
        return "x"

    async def go():
        return await ensure_awaitable(coro), await ensure_awaitable(coro)

    assert asyncio.run(go()) == ("x", "x")


def test_sync_callable_is_recallable():
    counter = [0]

    def sync_fn():
        counter[0] += 1
        return counter[0]

    async def go():
        a = await ensure_awaitable(sync_fn)
        b = await ensure_awaitable(sync_fn)
        return a, b

    assert asyncio.run(go()) == (1, 2)


def test_coroutine_object_is_one_shot():
    """A bare coroutine object can only be awaited once."""

    async def coro():
        return "x"

    async def go():
        co = coro()
        first = await ensure_awaitable(co)
        # second attempt fails because the inner coroutine is exhausted
        await ensure_awaitable(co)
        return first

    with pytest.raises(RuntimeError):
        asyncio.run(go())


# ---------------------------------------------------------------------------
# contextvars propagation: the caller's context must be visible inside the
# scheduled sync callable, because we copy the current context into
# loop.call_soon. Without that the call would run with the loop's own
# default context.
# ---------------------------------------------------------------------------

import contextvars  # noqa: E402

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="<unset>")


def test_sync_callable_sees_caller_contextvar():
    """A sync callable scheduled via ensure_awaitable observes the
    ``ContextVar`` value set by the caller."""

    def read_ctx():
        return _request_id.get()

    async def go():
        _request_id.set("req-1")
        return await ensure_awaitable(read_ctx)

    assert asyncio.run(go()) == "req-1"


def test_sync_callable_uses_snapshot_at_schedule_time():
    """``contextvars.copy_context()`` captures the *current* values; later
    mutation by the caller doesn't leak into the scheduled callable."""

    def read_ctx():
        return _request_id.get()

    async def go():
        _request_id.set("first")
        scheduled = ensure_awaitable(read_ctx)  # snapshot taken now
        _request_id.set("second")  # later mutation
        return await scheduled

    assert asyncio.run(go()) == "first"


def test_sync_callable_does_not_leak_writes_to_caller():
    """Writes to a ContextVar inside the scheduled callable stay in its
    copied context — the caller doesn't see them after the await."""

    def write_ctx():
        _request_id.set("written-by-callee")
        return "ok"

    async def go():
        _request_id.set("caller-value")
        result = await ensure_awaitable(write_ctx)
        return result, _request_id.get()

    assert asyncio.run(go()) == ("ok", "caller-value")


def test_async_callable_sees_caller_contextvar_naturally():
    """Async callables don't go through ``call_soon``; they pick up the
    caller's context through the normal asyncio inheritance."""

    async def read_ctx():
        return _request_id.get()

    async def go():
        _request_id.set("req-async")
        return await ensure_awaitable(read_ctx)

    assert asyncio.run(go()) == "req-async"


def test_concurrent_sync_callables_isolated_contexts():
    """Concurrent ensure_awaitable calls each get their own context
    snapshot, so writes don't leak across them."""

    seen = {}

    def make_reader(label):
        def read():
            seen[label] = _request_id.get()
            _request_id.set(f"mutated-by-{label}")
            return label

        return read

    async def task(label, value):
        _request_id.set(value)
        return await ensure_awaitable(make_reader(label))

    async def go():
        results = await asyncio.gather(
            task("A", "v-A"),
            task("B", "v-B"),
        )
        return results, seen

    results, snapshot = asyncio.run(go())
    assert set(results) == {"A", "B"}
    assert snapshot["A"] == "v-A"
    assert snapshot["B"] == "v-B"
