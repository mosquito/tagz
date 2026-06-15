from importlib.metadata import version as _pkg_version

project = "tagz"
author = "Dmitry Orlov"
copyright = "2025, Dmitry Orlov"

release = _pkg_version("tagz")
version = ".".join(release.split(".")[:2])

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinxcontrib.mermaid",
]

source_suffix = {".md": "markdown", ".rst": "restructuredtext"}

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "tasklist",
    "attrs_inline",
]
myst_heading_anchors = 3

html_theme = "furo"
html_title = "tagz"
html_static_path = ["_static"]
html_theme_options = {
    "source_repository": "https://github.com/mosquito/tagz",
    "source_branch": "master",
    "source_directory": "docs/",
    "sidebar_hide_name": False,
}

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_class_signature = "separated"
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    "undoc-members": False,
}

napoleon_google_docstring = True
napoleon_numpy_docstring = False

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
