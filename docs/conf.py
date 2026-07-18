# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))


def _register_mermaid_alias_to_text(_app):
    """Best-effort: register ``mermaid`` as a pygments lexer alias.

    ``pygments`` does not ship a ``mermaid`` lexer and the repo's diagram
    files use triple-backtick ``mermaid`` fences that Pygments then flags
    with a "Pygments lexer name 'mermaid' is not known" warning. This
    hook tries to add ``mermaid`` (and ``mmd``) as aliases of ``TextLexer``
    so the highlighter falls back to plain text. The Pages workflow uses
    Sphinx **without** ``-W`` so cosmetic warnings do not break the
    deploy; this is a defence-in-depth pass, not a guarantee.
    """
    try:
        import pygments.lexers
    except ImportError:
        return

    text_cls = pygments.lexers.TextLexer
    try:
        text_cls.aliases = tuple(set(getattr(text_cls, "aliases", ())) | {"mermaid", "mmd"})  # type: ignore[attr-defined]
    except AttributeError:
        return

    special = getattr(pygments.lexers, "SPECIAL_LEXERS", None)
    if isinstance(special, dict) and "TextLexer" in special:
        original = special["TextLexer"]
        try:
            name, _a, filenames, mimetypes = original
            special["TextLexer"] = (
                name,
                tuple(set(original[1]) | {"mermaid", "mmd"}),
                filenames,
                mimetypes,
            )
        except (IndexError, TypeError):
            pass


def setup(app):
    """Sphinx setup hook: register pygments aliases for unused lexer names."""
    _register_mermaid_alias_to_text(app)
    return {"version": "1.0", "parallel_read_safe": True}


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
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "myst_parser",
    "sphinxcontrib.mermaid",
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
