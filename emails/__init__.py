# coding: utf-8
from __future__ import unicode_literals
"""
python emails library
~~~~~~~~~~~~~~~~~~~~~

emails is a python library for dealing with html-emails.

Usage:

   >>> import emails
   >>> message = emails.html(html="<p>Hi!<br>Here is your receipt...",
                          subject="Your receipt No. 567098123",
                          mail_from=('Some Store', 'store@somestore.com'))
   >>> message.send( to = 's@lavr.me', smtp={ 'host': 'aspmx.l.google.com' } )


More examples is at <https://github.com/lavr/python-emails/README.rst>.

:copyright: (c) 2013 by Sergey Lavrinenko.
:license: Apache 2.0, see LICENSE for more details.

"""

__title__ = 'emails'
__version__ = '0.3.7'
__author__ = 'Sergey Lavrinenko'
__license__ = 'Apache 2.0'
__copyright__ = 'Copyright 2013-2015 Sergey Lavrinenko'

USER_AGENT = 'python-emails/%s' % __version__

from .message import Message, html
from .utils import MessageID


