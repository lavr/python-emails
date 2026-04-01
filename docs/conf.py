import sys, os
sys.path.append(os.path.abspath('_themes'))
sys.path.append(os.path.abspath('..'))
sys.path.append(os.path.abspath('.'))

from conf_base import *
from conf_theme_alabaster import *

#from conf_theme_flask import *

from emails import __version__ as _emails_version
version = '.'.join(_emails_version.split('.')[:2])
release = _emails_version
html_theme_path = ['_themes', ] + html_theme_path
