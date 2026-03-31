# encoding: utf-8
from __future__ import annotations

import sys
import os
import socket
from time import mktime
from datetime import datetime
from random import randrange
from functools import wraps
from io import StringIO, BytesIO
from collections.abc import Callable
from typing import Any, TypeVar, cast, overload

import email.charset
from email import generator
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header, decode_header as decode_header_
from email.utils import parseaddr, formatdate
from email.utils import escapesre, specialsre  # type: ignore[attr-defined]  # private but stable

from . import USER_AGENT
from .exc import HTTPLoaderError

F = TypeVar('F', bound=Callable[..., Any])


def to_native(x: str | bytes | None, charset: str = sys.getdefaultencoding(),
              errors: str = 'strict') -> str | None:
    if x is None or isinstance(x, str):
        return x
    return x.decode(charset, errors)


@overload
def to_unicode(x: None, charset: str = ..., errors: str = ...) -> None: ...
@overload
def to_unicode(x: str | bytes, charset: str = ..., errors: str = ...) -> str: ...
@overload
def to_unicode(x: Any, charset: str = ..., errors: str = ...) -> str | None: ...

def to_unicode(x: Any, charset: str = sys.getdefaultencoding(),
               errors: str = 'strict') -> str | None:
    if x is None:
        return None
    if not isinstance(x, bytes):
        return str(x)
    return x.decode(charset, errors)


def to_bytes(x: str | bytes | bytearray | memoryview | None,
             charset: str = sys.getdefaultencoding(),
             errors: str = 'strict') -> bytes | None:
    if x is None:
        return None
    if isinstance(x, (bytes, bytearray, memoryview)):
        return bytes(x)
    if isinstance(x, str):
        return x.encode(charset, errors)
    raise TypeError('Expected bytes')


def formataddr(pair: tuple[str | None, str]) -> str:
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


_charsets_loaded = False

CHARSETS_FIX = [
    ['windows-1251', 'QP', 'QP'],
    # koi8 should by send as Quoted Printable because of bad SpamAssassin reaction on base64 (2008)
    ['koi8-r', 'QP', 'QP'],
    ['utf-8', 'BASE64', 'BASE64']
]


def load_email_charsets() -> None:
    global _charsets_loaded
    if not _charsets_loaded:
        for (charset, header_enc, body_enc) in CHARSETS_FIX:
            email.charset.add_charset(charset,
                                      getattr(email.charset, header_enc),
                                      getattr(email.charset, body_enc),
                                      charset)


class cached_property:
    """
    A property that is only computed once per instance and then replaces itself
    with an ordinary attribute. Deleting the attribute resets the property.
    Source: https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76
    """  # noqa

    def __init__(self, func: Callable[..., Any]) -> None:
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj: Any, cls: type | None = None) -> Any:
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


# Django's CachedDnsName:
# Cached the hostname, but do it lazily: socket.getfqdn() can take a couple of
# seconds, which slows down the restart of the server.
class CachedDnsName:
    def __str__(self) -> str:
        return self.get_fqdn()

    def get_fqdn(self) -> str:
        if not hasattr(self, '_fqdn'):
            self._fqdn = socket.getfqdn()
        return self._fqdn


DNS_NAME = CachedDnsName()


def decode_header(value: str | bytes, default: str = "utf-8", errors: str = 'strict') -> str:
    """Decode the specified header value"""
    if isinstance(value, bytes):
        value = value.decode(default, errors)
    parts: list[str] = []
    for text, charset in decode_header_(value):
        if isinstance(text, bytes):
            parts.append(text.decode(charset or default, errors))
        else:
            parts.append(text)
    return "".join(parts)


class MessageID:
    """Returns a string suitable for RFC 2822 compliant Message-ID, e.g:
    <20020201195627.33539.96671@nightshade.la.mastaler.com>
    Optional idstring if given is a string used to strengthen the
    uniqueness of the message id.
    Based on django.core.mail.message.make_msgid
    """

    def __init__(self, domain: str | None = None, idstring: str | int | None = None) -> None:
        self.domain = str(domain or DNS_NAME)
        try:
            pid = os.getpid()
        except AttributeError:
            # No getpid() in Jython.
            pid = 1
        self.idstring = ".".join([str(idstring or randrange(10000)), str(pid)])

    def __call__(self) -> str:
        r = ".".join([datetime.now().strftime("%Y%m%d%H%M%S.%f"),
                      str(randrange(100000)),
                      self.idstring])
        return "".join(['<', r, '@', self.domain, '>'])


# Type alias for address pairs used throughout the library
AddressPair = tuple[str | None, str | None]


def parse_name_and_email_list(elements: str | tuple[str | None, str] | list[Any] | None,
                              encoding: str = 'utf-8') -> list[AddressPair]:
    """
    Parse a list of address-like elements, i.e.:
     * "name <email>"
     * "email"
     * (name, email)

    :param elements: one element or list of elements
    :param encoding: element encoding, if bytes
    :return: list of pairs (name, email)
    """
    if not elements:
        return []

    if isinstance(elements, str):
        return [parse_name_and_email(elements, encoding), ]

    if not isinstance(elements, (list, tuple)):
        raise TypeError("Can not parse_name_and_email_list from %s" % elements.__repr__())

    if len(elements) == 2:
        # Oops, it may be pair (name, email) or pair of emails [email1, email2]
        # Let's do some guesses
        if isinstance(elements, tuple):
            n, e = elements
            if isinstance(e, str) and (not n or isinstance(n, str)):
                # It is probably a pair (name, email)
                return [parse_name_and_email(elements, encoding), ]

    return [parse_name_and_email(x, encoding) for x in elements]


def parse_name_and_email(obj: str | tuple[str | None, str] | list[str],
                         encoding: str = 'utf-8') -> AddressPair:
    # In:  'john@smith.me' or  '"John Smith" <john@smith.me>' or ('John Smith', 'john@smith.me')
    # Out: (u'John Smith', u'john@smith.me')

    if isinstance(obj, (list, tuple)):
        if len(obj) == 2:
            name, email = obj
        else:
            raise ValueError("Can not parse_name_and_email from %s" % obj)
    elif isinstance(obj, str):
        name, email = parseaddr(obj)
    else:
        raise ValueError("Can not parse_name_and_email from %s" % obj)

    return name or None, email or None


def sanitize_email(addr: str, encoding: str = 'ascii', parse: bool = False) -> str:
    if parse:
        _, addr = parseaddr(addr)
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
    return addr


def sanitize_address(addr: str | tuple[str, str], encoding: str = 'ascii') -> str:
    if isinstance(addr, str):
        addr = parseaddr(addr)
    nm, addr = addr
    # This try-except clause is needed on Python 3 < 3.2.4
    # http://bugs.python.org/issue14291
    try:
        nm = Header(nm, encoding).encode()
    except UnicodeEncodeError:
        nm = Header(nm, 'utf-8').encode()
    return formataddr((nm, sanitize_email(addr, encoding=encoding, parse=False)))


class MIMEMixin:
    def as_string(self, unixfrom: bool = False, linesep: str = '\n') -> str:
        """Return the entire formatted message as a string.
        Optional `unixfrom' when True, means include the Unix From_ envelope
        header.
        This overrides the default as_string() implementation to not mangle
        lines that begin with 'From '. See bug #13433 for details.
        """
        fp = StringIO()
        g = generator.Generator(fp, mangle_from_=False)
        g.flatten(self, unixfrom=unixfrom, linesep=linesep)

        return fp.getvalue()

    def as_bytes(self, unixfrom: bool = False, linesep: str = '\n') -> bytes:
            """Return the entire formatted message as bytes.
            Optional `unixfrom' when True, means include the Unix From_ envelope
            header.
            This overrides the default as_bytes() implementation to not mangle
            lines that begin with 'From '. See bug #13433 for details.
            """
            fp = BytesIO()
            g = generator.BytesGenerator(fp, mangle_from_=False)
            g.flatten(self, unixfrom=unixfrom, linesep=linesep)
            return fp.getvalue()


class SafeMIMEText(MIMEMixin, MIMEText):  # type: ignore[misc]  # intentional override
    def __init__(self, text: str, subtype: str, charset: str) -> None:
        self.encoding = charset
        MIMEText.__init__(self, text, subtype, charset)


class SafeMIMEMultipart(MIMEMixin, MIMEMultipart):  # type: ignore[misc]  # intentional override
    def __init__(self, _subtype: str = 'mixed', boundary: str | None = None,
                 _subparts: list[Any] | None = None,
                 encoding: str | None = None, **_params: Any) -> None:
        self.encoding = encoding
        MIMEMultipart.__init__(self, _subtype, boundary, _subparts, **_params)


DEFAULT_REQUESTS_PARAMS: dict[str, Any] = dict(allow_redirects=True,
                             verify=False, timeout=10,
                             headers={'User-Agent': USER_AGENT})


def fetch_url(url: str, valid_http_codes: tuple[int, ...] = (200, ),
              requests_args: dict[str, Any] | None = None) -> Any:
    import requests
    args = {}
    args.update(DEFAULT_REQUESTS_PARAMS)
    args.update(requests_args or {})
    r = requests.get(url, **args)
    if valid_http_codes and (r.status_code not in valid_http_codes):
        raise HTTPLoaderError('Error loading url: %s. HTTP status: %s' % (url, r.status_code))
    return r


def encode_header(value: str | Any, charset: str = 'utf-8') -> str | Any:
    if isinstance(value, str):
        value = value.rstrip()
        _r = Header(value, charset)
        return str(_r)
    else:
        return value


def renderable(f: F) -> F:
    @wraps(f)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        r = f(self, *args, **kwargs)
        render = getattr(r, 'render', None)
        if render:
            d = render(**(self.render_data or {}))
            return d
        else:
            return r

    return cast(F, wrapper)


def format_date_header(v: datetime | float | None, localtime: bool = True) -> str:
    if isinstance(v, datetime):
        return formatdate(mktime(v.timetuple()), localtime)
    elif isinstance(v, float):
        # probably timestamp
        return formatdate(v, localtime)
    elif v is None:
        return formatdate(None, localtime)
    else:
        return v
