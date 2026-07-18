# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))


# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "QKDpy"
copyright = "2024-2026, Pranava-Kumar"
author = "Pranava-Kumar"
release = "0.6.6"
version = "0.6.6"
language = "en"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "myst_parser",
]

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "dollarmath",
    "replacements",
    "smartquotes",
    "substitution",
    "tasklist",
]

templates_path = ["_templates"]
exclude_patterns = [
    "_build",
    "_static",
    "Thumbs.db",
    ".DS_Store",
    "source/*",
    "source/**/*",
    # Engineering / maintainer-only material. Lives in the repo for the
    # developer and AI agents but is not exposed on the public Pages
    # site because it carries internal architecture sources, raw
    # diagram code, and the open-core / commercial tier details.
    "decisions/*",
    "diagrams/*.md",
    "OPEN_CORE.md",
    "NEXT_STEPS.md",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_title = "QKDpy v0.6.6 — Quantum Key Distribution library"
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_show_sourcelink = False
html_last_updated_fmt = "%Y-%m-%d"
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 4,
    "prev_next_buttons_location": "bottom",
}

# -- Autodoc configuration ---------------------------------------------------
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "exclude-members": "__weakref__",
}
