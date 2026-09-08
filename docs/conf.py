"""Sphinx configuration for the docs site.

The pages themselves are plain Markdown, parsed by MyST rather than written in
reStructuredText — see https://myst-parser.readthedocs.io/. This file is read
by both `sphinx-build` locally and Read the Docs; neither imports the project,
so it does not need to be installed to build the docs.
"""

from __future__ import annotations

project = "motioninput-tui"
copyright = "kism"  # ruff: ignore[builtin-variable-shadowing] - the name Sphinx's conf.py convention expects
author = "kism"

extensions = ["myst_parser"]

source_suffix = {
    ".md": "markdown",
}

# The landing page. Sphinx calls this the "root doc"; it is docs/index.md.
root_doc = "index"

# Relative links between pages (`[Adding a game](adding-a-game.md)`) are
# resolved by MyST as cross-references automatically. This just adds `#slug`
# anchors on headings, which the pages also link to directly.
myst_heading_anchors = 3

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "sphinx_rtd_theme"
