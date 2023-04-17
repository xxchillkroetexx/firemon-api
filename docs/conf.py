# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "firemon-api"
copyright = "2023, Luke Johannsen"
author = "Luke Johannsen"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]
html_logo = "logo_firemon.png"
html_theme_options = {
    "show_powered_by": False,
    "github_banner": True,
    "show_related": False,
    "note_bg": "#FFF59C",
}

# If true, links to the reST sources are added to the pages.
html_show_sourcelink = False

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = True


# Custom sidebar templates, maps document names to template names.
html_sidebars = {
    "index": ["sidebarintro.html", "sourcelink.html", "searchbox.html"],
    "**": ["sidebarlogo.html", "sourcelink.html", "searchbox.html"],
}
