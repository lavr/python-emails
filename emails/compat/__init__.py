# -*- coding: utf-8 -*-
import sys
import urllib.parse as urlparse
from collections import OrderedDict
from collections.abc import Callable
from io import StringIO, BytesIO

from email.utils import escapesre, specialsre

NativeStringIO = StringIO

string_types = (str, )
text_type = str


def to_native(x, charset=sys.getdefaultencoding(), errors='strict'):
    if x is None or isinstance(x, str):
        return x
    return x.decode(charset, errors)


def to_unicode(x, charset=sys.getdefaultencoding(), errors='strict',
               allow_none_charset=False):
    if x is None:
        return None
    if not isinstance(x, bytes):
        return str(x)
    if charset is None and allow_none_charset:
        return x
    return x.decode(charset, errors)


def to_bytes(x, charset=sys.getdefaultencoding(), errors='strict'):
    if x is None:
        return None
    if isinstance(x, (bytes, bytearray, memoryview)):
        return bytes(x)
    if isinstance(x, str):
        return x.encode(charset, errors)
    raise TypeError('Expected bytes')


def is_callable(x):
    return isinstance(x, Callable)


def formataddr(pair):
    """
    Takes a 2-tuple of the form (realname, email_address) and returns RFC2822-like string.
    Does not encode non-ascii realname (unlike stdlib email.utils.formataddr).
    """
    name, address = pair
    if name:
        quotes = ''
        if specialsre.search(name):
            quotes = '"'
        name = escapesre.sub(r'\\\g<0>', name)
        return '%s%s%s <%s>' % (quotes, name, quotes, address)
    return address
