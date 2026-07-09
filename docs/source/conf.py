"""Sphinx configuration for QKDpy."""

import os
import sys

sys.path.insert(0, os.path.abspath("../../src"))

project = "QKDpy"
copyright = "2026, Pranava Kumar"
author = "Pranava Kumar"
release = "0.4.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_rtd_theme",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = []
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "scipy": ("https://docs.scipy.org/doc/scipy", None),
}

# Autodoc settings
autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
    "special-members": "__init__",
}
autodoc_typehints = "description"
napoleon_google_docstring = True
napoleon_numpy_docstring = False

# MyST settings
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
