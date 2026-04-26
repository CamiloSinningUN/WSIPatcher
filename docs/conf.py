import os
import sys
from typing import Any

sys.path.insert(0, os.path.abspath(".."))

project = "GlassCut"
copyright = "2025, Camilo Jose Sinning Lopez"
author = "Camilo Jose Sinning Lopez"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.mathjax",
    "sphinx_copybutton",
    "sphinx_design",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "PIL": ("https://pillow.readthedocs.io/en/stable", None),
    "skimage": ("https://scikit-image.org/docs/stable", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "shibuya"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_js_files = ["custom.js"]
html_title = "GlassCut"

html_theme_options: dict[str, Any] = {
    "github_url": "https://github.com/CamiloSinningUN/GlassCut",
    "color_mode": "dark",
    "accent_color": "iris",
    "light_logo": "_static/web-light/icons8-scissors-led-32.png",
    "dark_logo": "_static/web-dark/icons8-scissors-led-32.png",
    "nav_links": [
        {
            "title": "Installation",
            "url": "installation",
        },
        {
            "title": "Quickstart",
            "url": "quickstart",
        },
        {
            "title": "Usage",
            "url": "usage/index",
            "children": [
                {
                    "title": "Slides",
                    "url": "usage/slides",
                },
                {
                    "title": "Tiling",
                    "url": "usage/tiling",
                },
                {
                    "title": "Tissue Detection",
                    "url": "usage/tissue_detection",
                },
                {
                    "title": "Stain Normalization",
                    "url": "usage/stain_normalization",
                },
                {
                    "title": "Dataset",
                    "url": "usage/dataset",
                },
                {
                    "title": "Sample Data",
                    "url": "usage/data",
                },
            ],
        },
        {
            "title": "API",
            "url": "api/index",
        },
        {
            "title": "Contributing",
            "url": "contributing",
        },
    ],
}

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_attr_annotations = True

autodoc_default_options: dict[str, Any] = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__",
    "undoc-members": True,
    "show-inheritance": True,
}

autodoc_typehints = "description"
