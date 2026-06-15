# Minimal Sphinx Makefile.

SPHINXOPTS    ?=
SPHINXBUILD   ?= uv run sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Default target: show help.
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

# Strict HTML build — turns Sphinx warnings into errors, matches CI.
strict:
	$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" -W $(SPHINXOPTS)

# Live-reload server: edits in docs/ rebuild and refresh the browser.
live:
	uv run sphinx-autobuild "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS)

.PHONY: help strict live Makefile

# Catch-all: forward any other target (clean, html, linkcheck, …) to sphinx-build.
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
