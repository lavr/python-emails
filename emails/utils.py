# encoding: utf-8

__all__ = ['parse_name_and_email', 'SMTPConnectionPool', 'DomainKeySigner']

from email.parser import HeaderParser
from email.utils import parseaddr
import smtplib
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


def GetSMTP(*args, **kwargs):
    is_ssl = kwargs.pop('ssl', False)
    user = kwargs.pop('user', None)
    password = kwargs.pop('password', None)
    debug = kwargs.pop('debug', False)
    if is_ssl:
        r = smtplib.SMTP_SSL(**kwargs)
    else:
        r = smtplib.SMTP(**kwargs)

    if debug:
        r.set_debuglevel(1)
    if user:
        r.login(user=user, password=password)

    return r


def serialize_dict(d):
    # simple dict serializer
    r = []
    for (k, v) in d.iteritems():
        r.append("%s=%s" % (k, v))
    return ";".join(r)


class SMTPConnectionPool:

    smtp_cls = GetSMTP

    def __init__(self):
        self.pool = {}

    def __getitem__(self, k):

        if not isinstance(k, dict):
            raise ValueError("item must be dict, not %s" % type(k))

        kk = serialize_dict(k)

        r = self.pool.get(kk, None)

        if r is None:
            r = self.smtp_cls(**k)
            self.pool[kk] = r

        return r

    def reconnect(self, k):

        kk = serialize_dict(k)

        if kk in self.pool:
            del self.pool[kk]

        return self[k]


def test_parse_name_and_email():
    assert parse_name_and_email('john@smith.me') == (u'', u'john@smith.me')
    assert parse_name_and_email('"John Smith" <john@smith.me>') == \
                               (u'John Smith', u'john@smith.me')
    assert parse_name_and_email(['John Smith', 'john@smith.me']) == \
                               (u'John Smith', u'john@smith.me')


if __name__ == '__main__':
    test_parse_name_and_email()
