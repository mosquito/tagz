# Explanation

Background, design rationale, and the conceptual model behind `tagz`.
Read these when you want to understand *why* the library behaves the
way it does — not how to call it.

```{toctree}
:maxdepth: 1

why-no-templates
architecture
escaping-model
rendering-and-streaming
callables-and-laziness
async-and-tagz
```

## What's here?

- **[Why no templates?](why-no-templates.md)** — the case for
  Python-as-template and where Jinja2 still wins.
- **[Architecture](architecture.md)** — the class hierarchy:
  `Tag`, `TagInstance`, `Fragment`, `Raw`, `Page`, and how they relate.
- **[The escaping model](escaping-model.md)** — exactly where
  `html.escape()` is called, and why `<script>` and `<style>` are
  exceptions.
- **[Rendering and streaming](rendering-and-streaming.md)** — the
  three iter-methods, what `pretty=True` does and doesn't promise.
- **[Callables and laziness](callables-and-laziness.md)** — when
  callables run, how often, and what that means for side effects.
- **[Async and `tagz`](async-and-tagz.md)** — the `tagz.aio` mirror
  with async render and streaming via `iter_chunk` / `iter_lines`.
