import sys
import os

sys.path.append(os.path.abspath('..'))

# -- General configuration ------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.coverage',
    'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode',
    'sphinx_togglebutton',
]

templates_path = ['_templates']
source_suffix = '.rst'
master_doc = 'index'

project = 'python-emails'
copyright = '2015-2026, Sergey Lavrinenko'

from emails import __version__ as _emails_version
version = '.'.join(_emails_version.split('.')[:2])
release = _emails_version

exclude_patterns = ['_build', 'examples.rst']
pygments_style = 'sphinx'

# -- Options for HTML output ----------------------------------------------

html_theme = 'furo'

html_theme_options = {
    "source_repository": "https://github.com/lavr/python-emails",
    "source_branch": "master",
    "source_directory": "docs/",
    "navigation_with_keys": True,
}

html_title = f"python-emails {release}"

html_static_path = ['_static']

htmlhelp_basename = 'python-emailsdoc'

# -- Options for LaTeX output ---------------------------------------------

latex_elements = {}

latex_documents = [
    ('index', 'python-emails.tex', 'python-emails Documentation',
     'Sergey Lavrinenko', 'manual'),
]

# -- Options for manual page output ---------------------------------------

man_pages = [
    ('index', 'python-emails', 'python-emails Documentation',
     ['Sergey Lavrinenko'], 1)
]

# -- Options for Texinfo output -------------------------------------------

texinfo_documents = [
    ('index', 'python-emails', 'python-emails Documentation',
     'Sergey Lavrinenko', 'python-emails',
     'Modern email handling in python.',
     'Miscellaneous'),
]

# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}
