import sys, os
sys.path.append(os.path.abspath('_themes'))
sys.path.append(os.path.abspath('.'))

from conf_base import *
from conf_theme_alabaster import *

#from conf_theme_flask import *

html_theme_path = ['_themes', ] + html_theme_path
