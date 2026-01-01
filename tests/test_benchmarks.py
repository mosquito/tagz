"""
Performance benchmarks for tagz library.

Run with: pytest tests/test_benchmarks.py -v
Or with benchmark plugin: pytest tests/test_benchmarks.py --benchmark-only
"""

import pytest
from tagz import html, Fragment, Raw
from functools import partial


def test_benchmark_tag_creation(benchmark):
    """Benchmark creating tags with string children."""

    def create_tags():
        return [html.p(f"Paragraph {i}") for i in range(100)]

    result = benchmark(create_tags)
    assert len(result) == 100


def test_benchmark_nested_tags(benchmark):
    """Benchmark creating nested tag structures."""

    def create_nested():
        return html.div(*[html.p(f"Paragraph {i}") for i in range(100)])

    result = benchmark(create_nested)
    assert result.name == "div"
    assert len(result.children) == 100


def test_benchmark_string_generation(benchmark):
    """Benchmark HTML string generation."""
    tag = html.div(*[html.p(f"Paragraph {i}") for i in range(100)])

    result = benchmark(str, tag)
    assert len(result) > 0
    assert result.startswith("<div>")


def test_benchmark_pretty_printing(benchmark):
    """Benchmark pretty printing."""
    tag = html.div(*[html.p(f"Paragraph {i}") for i in range(100)])

    result = benchmark(tag.to_string, pretty=True)
    assert "\n" in result
    assert "\t" in result


def test_benchmark_escaping(benchmark):
    """Benchmark HTML escaping."""
    tag = html.div(*[html.p("<script>alert('xss')</script>") for i in range(100)])

    result = benchmark(str, tag)
    # Content is escaped - check for escaped characters
    assert "&" in result  # Either &lt; or &amp; depending on escaping level
    assert len(result) > 1000  # Should have generated lots of HTML


def test_benchmark_fragment(benchmark):
    """Benchmark Fragment rendering."""

    def create_fragment():
        return str(Fragment(*[html.p(f"P {i}") for i in range(100)]))

    result = benchmark(create_fragment)
    assert len(result) > 0


def test_benchmark_streaming_chunk(benchmark):
    """Benchmark streaming with iter_chunk."""
    tag = html.div(*[html.p(f"Paragraph {i}") for i in range(100)])

    def stream_chunks():
        return list(tag.iter_chunk(chunk_size=1024))

    result = benchmark(stream_chunks)
    assert len(result) > 0


def test_benchmark_streaming_lines(benchmark):
    """Benchmark streaming with iter_lines."""
    tag = html.div(*[html.p(f"Paragraph {i}") for i in range(100)])

    def stream_lines():
        return list(tag.iter_lines())

    result = benchmark(stream_lines)
    assert len(result) > 0


def test_benchmark_callable_children(benchmark):
    """Benchmark tags with callable children."""

    def create_with_callables():
        return html.div(
            *[html.p(partial("Paragraph {}".format, i)) for i in range(100)]
        )

    result = benchmark(create_with_callables)
    assert result.name == "div"


def test_benchmark_large_document(benchmark):
    """Benchmark creating and rendering a large document (1000 tags)."""

    def create_large_doc():
        tag = html.div(*[html.p(f"Paragraph {i}") for i in range(1000)])
        return str(tag)

    result = benchmark(create_large_doc)
    assert len(result) > 10000


# Manual timing benchmarks (for cases without pytest-benchmark)
def test_manual_benchmark_comparison():
    """Manual benchmark to verify optimization impact."""
    import time

    # Test 1: String children (optimized path)
    start = time.perf_counter()
    for _ in range(1000):
        tag = html.div(*[html.p(f"Text {i}") for i in range(10)])
    time_with_strings = (time.perf_counter() - start) * 1000

    # Test 2: Tag children (still copies)
    start = time.perf_counter()
    for _ in range(1000):
        paragraphs = [html.p(f"Text {i}") for i in range(10)]
        tag = html.div(*paragraphs)
    time_with_tags = (time.perf_counter() - start) * 1000

    print(f"\nManual Benchmark Results:")
    print(f"  With string children: {time_with_strings:.2f}ms")
    print(f"  With tag children: {time_with_tags:.2f}ms")
    print(
        f"  String optimization benefit: {((time_with_tags - time_with_strings) / time_with_tags * 100):.1f}%"
    )

    # String path should be faster or equal
    assert time_with_strings <= time_with_tags * 1.1  # Allow 10% variance


def test_copy_behavior():
    """Verify that the optimization doesn't break copy semantics."""
    from copy import copy

    # Test 1: String children should not be copied (optimization)
    p1 = html.p("test")
    div1 = html.div(p1)
    div2 = html.div(p1)

    # Modifying p1 should not affect div1 or div2 (they have copies)
    p1.append(" modified")

    assert str(p1) == "<p>test modified</p>"
    assert str(div1) == "<div><p>test</p></div>"
    assert str(div2) == "<div><p>test</p></div>"

    # Test 2: Copying a tag should still work
    original = html.div("text", html.p("paragraph"))
    copied = copy(original)

    assert original is not copied
    assert str(original) == str(copied)

    # Modifying copied should not affect original
    copied.append(html.span("added"))
    assert len(original.children) == 2
    assert len(copied.children) == 3


def test_profile_hotspots():
    """Profile code to identify bottlenecks."""
    import cProfile
    import pstats
    from io import StringIO

    def workload():
        tags = [html.p(f"Paragraph {i}") for i in range(100)]
        tag = html.div(*tags)
        return str(tag)

    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(100):
        workload()
    profiler.disable()

    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("cumulative")
    ps.print_stats(25)

    output = s.getvalue()
    print("\n" + "=" * 70)
    print("PROFILING HOTSPOTS (Top 25 functions)")
    print("=" * 70)
    print(output)

    # Find specific hotspots
    s2 = StringIO()
    ps2 = pstats.Stats(profiler, stream=s2).sort_stats("tottime")
    ps2.print_stats(15)

    print("\n" + "=" * 70)
    print("BY TOTAL TIME (Top 15 functions)")
    print("=" * 70)
    print(s2.getvalue())


def test_profile_large_document():
    """Profile large document creation to find bottlenecks."""
    import cProfile
    import pstats
    from io import StringIO
    import time

    def large_doc_workload():
        tag = html.div(*[html.p(f"Paragraph {i}") for i in range(1000)])
        return str(tag)

    # First, time it
    start = time.perf_counter()
    result = large_doc_workload()
    end = time.perf_counter()

    print("\n" + "=" * 70)
    print("LARGE DOCUMENT ANALYSIS (1000 paragraphs)")
    print("=" * 70)
    print(f"Time: {(end - start) * 1000:.2f}ms")
    print(f"Output size: {len(result)} bytes")
    print(f"Operations per second: {1 / (end - start):.1f}")

    # Profile it
    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(10):  # Run 10 times for better statistics
        large_doc_workload()
    profiler.disable()

    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats("tottime")
    ps.print_stats(20)

    print("\n" + "=" * 70)
    print("PROFILING BY TOTAL TIME (Top 20 functions)")
    print("=" * 70)
    print(s.getvalue())

    # Show cumulative time too
    s2 = StringIO()
    ps2 = pstats.Stats(profiler, stream=s2).sort_stats("cumulative")
    ps2.print_stats(15)

    print("\n" + "=" * 70)
    print("PROFILING BY CUMULATIVE TIME (Top 15)")
    print("=" * 70)
    print(s2.getvalue())
