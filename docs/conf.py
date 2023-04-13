"""Sphinx configuration."""
project = "Archive Cp"
author = "Christopher Larson"
copyright = "2023, Christopher Larson"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx_click",
    "myst_parser",
]
autodoc_typehints = "description"
html_theme = "furo"
