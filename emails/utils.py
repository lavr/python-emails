# encoding: utf-8
from __future__ import unicode_literals

__all__ = ['parse_name_and_email', 'load_email_charsets', 'MessageID']

import socket
import time
import os
import random
import email.charset

from email.generator import Generator
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr, parseaddr

from emails.compat import string_types, to_unicode, NativeStringIO

_charsets_loaded = False

CHARSETS_FIX = [
    ['windows-1251', 'QP', 'QP'],
    # koi8 should by send as Quoted Printable because of bad SpamAssassin reaction on base64 (2008)
    ['koi8-r', 'QP', 'QP'],
    ['utf-8', 'BASE64', 'BASE64']
]


def load_email_charsets():
    global _charsets_loaded
    if not _charsets_loaded:
        for (charset, header_enc, body_enc) in CHARSETS_FIX:
            email.charset.add_charset(charset,
                                      getattr(email.charset, header_enc),
                                      getattr(email.charset, body_enc),
                                      charset)


# Django's CachedDnsName:
# Cached the hostname, but do it lazily: socket.getfqdn() can take a couple of
# seconds, which slows down the restart of the server.
class CachedDnsName(object):
    def __str__(self):
        return self.get_fqdn()

    def get_fqdn(self):
        if not hasattr(self, '_fqdn'):
            self._fqdn = socket.getfqdn()
        return self._fqdn


DNS_NAME = CachedDnsName()


class MessageID:
    """Returns a string suitable for RFC 2822 compliant Message-ID, e.g:

    <20020201195627.33539.96671@nightshade.la.mastaler.com>

    Optional idstring if given is a string used to strengthen the
    uniqueness of the message id.

    Based on django.core.mail.message.make_msgid
    """

    def __init__(self, domain=None, idstring=None):
        self.domain = domain or DNS_NAME
        self.idstring = idstring

    def __call__(self):
        timeval = time.time()
        utcdate = time.strftime('%Y%m%d%H%M%S', time.gmtime(timeval))
        try:
            pid = os.getpid()
        except AttributeError:
            # No getpid() in Jython, for example.
            pid = 1
        randint = random.randrange(100000)
        if self.idstring is None:
            idstring = ''
        else:
            idstring = '.' + self.idstring
        msgid = '<%s.%s.%s%s@%s>' % (utcdate, pid, randint, idstring, self.domain)
        return msgid


def parse_name_and_email(obj, encoding='utf-8'):
    # In:  'john@smith.me' or  '"John Smith" <john@smith.me>' or ('John Smith', 'john@smith.me')
    # Out: (u'John Smith', u'john@smith.me')

    _realname = ''
    _email = ''

    if isinstance(obj, (list, tuple)):
        if len(obj) == 2:
            _realname, _email = obj

    elif isinstance(obj, string_types):
        _realname, _email = parseaddr(obj)

    else:
        raise ValueError("Can not parse_name_and_email from %s" % obj)

    if isinstance(_realname, bytes):
        _realname = to_unicode(_realname, encoding)

    if isinstance(_email, bytes):
        _email = to_unicode(_email, encoding)

    return _realname or None, _email or None


def sanitize_address(addr, encoding):
    if isinstance(addr, string_types):
        addr = parseaddr(to_unicode(addr))
    nm, addr = addr
    # This try-except clause is needed on Python 3 < 3.2.4
    # http://bugs.python.org/issue14291
    try:
        nm = Header(nm, encoding).encode()
    except UnicodeEncodeError:
        nm = Header(nm, 'utf-8').encode()
    try:
        addr.encode('ascii')
    except UnicodeEncodeError:  # IDN
        if '@' in addr:
            localpart, domain = addr.split('@', 1)
            localpart = str(Header(localpart, encoding))
            domain = domain.encode('idna').decode('ascii')
            addr = '@'.join([localpart, domain])
        else:
            addr = Header(addr, encoding).encode()
    return formataddr((nm, addr))


class SafeMIMEText(MIMEText):
    def __init__(self, text, subtype, charset):
        self.encoding = charset
        MIMEText.__init__(self, text, subtype, charset)

    def __setitem__(self, name, val):
        MIMEText.__setitem__(self, name, val)

    def as_string(self, unixfrom=False):
        """Return the entire formatted message as a string.
        Optional `unixfrom' when True, means include the Unix From_ envelope
        header.

        This overrides the default as_string() implementation to not mangle
        lines that begin with 'From '. See bug #13433 for details.
        """
        fp = NativeStringIO()
        g = Generator(fp, mangle_from_=False)
        g.flatten(self, unixfrom=unixfrom)
        return fp.getvalue()


class SafeMIMEMultipart(MIMEMultipart):
    def __init__(self, _subtype='mixed', boundary=None, _subparts=None, encoding=None, **_params):
        self.encoding = encoding
        MIMEMultipart.__init__(self, _subtype, boundary, _subparts, **_params)

    def __setitem__(self, name, val):
        MIMEMultipart.__setitem__(self, name, val)

    def as_string(self, unixfrom=False):
        """Return the entire formatted message as a string.
        Optional `unixfrom' when True, means include the Unix From_ envelope
        header.

        This overrides the default as_string() implementation to not mangle
        lines that begin with 'From '. See bug #13433 for details.
        """
        fp = NativeStringIO()
        g = Generator(fp, mangle_from_=False)
        g.flatten(self, unixfrom=unixfrom)
        return fp.getvalue()


def test_parse_name_and_email():
    assert parse_name_and_email('john@smith.me') == ('', 'john@smith.me')
    assert parse_name_and_email('"John Smith" <john@smith.me>') == \
           ('John Smith', 'john@smith.me')
    assert parse_name_and_email(['John Smith', 'john@smith.me']) == \
           ('John Smith', 'john@smith.me')

