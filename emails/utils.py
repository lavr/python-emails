# encoding: utf-8

__all__ = [ 'parse_name_and_email', 'load_email_charsets' ]

from email.parser import HeaderParser
from email.utils import parseaddr
import email.charset

_charsets_loaded = False

CHARSETS = [
             ['windows-1251', 'QP', 'QP'],
             # koi8 should by send as Quoted Printable because of bad SpamAssassin reaction on base64 (in 2008)
             ['koi8-r', 'QP', 'QP'],
             ['utf-8', 'SHORTEST', 'BASE64']
            ]

def load_email_charsets():
    global _charsets_loaded
    if not _charsets_loaded:
        for (charset, header_enc, body_enc) in CHARSETS:
            email.charset.add_charset(charset,
                                      getattr(email.charset, header_enc),
                                      getattr(email.charset, body_enc))


def parse_name_and_email(obj, encoding='utf-8'):
    # In:  'john@smith.me' or  '"John Smith" <john@smith.me>' or ('John Smith', 'john@smith.me')
    # Out: (u'John Smith', u'john@smith.me')

    _realname = ''
    _email = ''

    if isinstance(obj, (list, tuple)):
        if len(obj) == 2:
            _realname, _email = obj

    elif isinstance(obj, basestring):
        _realname, _email = parseaddr(obj)

    else:
        raise ValueError("Can not parse_name_and_email from %s" % obj)

    return unicode(_realname, encoding), unicode(_email, encoding)



def test_parse_name_and_email():
    assert parse_name_and_email('john@smith.me') == (u'', u'john@smith.me')
    assert parse_name_and_email('"John Smith" <john@smith.me>') == \
                               (u'John Smith', u'john@smith.me')
    assert parse_name_and_email(['John Smith', 'john@smith.me']) == \
                               (u'John Smith', u'john@smith.me')

