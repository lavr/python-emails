# coding: utf-8
from __future__ import unicode_literals, print_function
import datetime
from email.utils import parseaddr
from dateutil.parser import parse as dateutil_parse
import pytest

import emails
from emails import Message
import emails.exc
from emails.compat import to_unicode, StringIO, is_py2, is_py34_plus
from emails.utils import decode_header, MessageID
from emails.backend.inmemory import InMemoryBackend

from .helpers import common_email_data


def test_message_types():
    m = emails.Message(**common_email_data())
    assert isinstance(m.as_string(), str)


def test_message_build():

    # Test simple build
    m = emails.Message(**common_email_data())
    assert m.as_string()

    # If no html or text - raises ValueError
    with pytest.raises(ValueError):
        emails.Message().as_string()

    # Test file-like html and text
    m = emails.Message(html=StringIO('X'), text=StringIO('Y'))
    assert m.html == 'X'
    assert m.text == 'Y'


def test_date():

    # default date is "current timestamp"
    m = emails.Message()
    assert dateutil_parse(m.date).replace(tzinfo=None) >= datetime.datetime.utcnow() - datetime.timedelta(seconds=3)

    # check date as constant
    m.date = '2015-01-01'
    assert m.date == '2015-01-01'
    assert m.message_date == m.date  # message_date is legacy

    # check date as func with string result
    m.date = lambda **kw: 'D'
    assert m.date == 'D'

    # check date as func with time result
    m.date = lambda **kw: 1426339147.572459
    assert 'Mar 2015' in m.date

    # check date as func with datetime result
    m.date = lambda **kw: datetime.datetime(2015, 1, 1)
    assert m.date.startswith('Thu, 01 Jan 2015 00:00:00')


def test_after_build():

    AFTER_BUILD_HEADER = 'X-After-Build'

    def my_after_build(original_message, built_message):
        built_message[AFTER_BUILD_HEADER] = '1'

    kwargs = common_email_data()
    m = emails.Message(**kwargs)
    m.after_build = my_after_build

    s = m.as_string()
    print("type of message.as_string() is {0}".format(type(s)))
    assert AFTER_BUILD_HEADER in to_unicode(s, 'utf-8')


def test_before_build():

    def my_before_build(message):
        message.render_data['x-before-build'] = 1

    m = emails.Message(**common_email_data())
    m.before_build = my_before_build

    s = m.as_string()
    assert m.render_data['x-before-build'] == 1


def test_sanitize_header():
    for header, value in (
            ('subject', 'test\n'),
            ('headers', {'X-Header': 'test\r'}),
            ):
        with pytest.raises(emails.exc.BadHeaderError):
            print('header {0}'.format(header))
            emails.Message(html='...', **{header: value}).as_message()


def test_headers_not_double_encoded():

    TEXT = '웃'

    m = Message()
    m.mail_from = (TEXT, 'a@b.c')
    m.mail_to = (TEXT, 'a@b.c')
    m.subject = TEXT
    m.html = '...'
    msg = m.as_message()
    assert decode_header(parseaddr(msg['From'])[0]) == TEXT
    assert decode_header(parseaddr(msg['To'])[0]) == TEXT
    assert decode_header(msg['Subject']) == TEXT


def test_headers_ascii_encoded():
    """
    Test we encode To/From header only when it not-ascii
    """

    for text, encoded in (
        ('웃', '=?utf-8?b?7JuD?='),
        ('ascii text', 'ascii text'),
    ):
        msg = Message(mail_from=(text, 'a@b.c'),
                      mail_to=(text, 'a@b.c'),
                      subject=text,
                      html='...').as_message()
        assert parseaddr(msg['From'])[0] == encoded
        assert parseaddr(msg['To'])[0] == encoded


def test_message_addresses():

    m = Message()

    m.mail_from = "웃 <b@c.d>"
    assert m.mail_from == ("웃", "b@c.d")

    m.mail_from = ["웃", "b@c.d"]
    assert m.mail_from == ("웃", "b@c.d")

    m.mail_to = ("웃", "b@c.d")
    assert m.mail_to == [("웃", "b@c.d"), ]

    m.mail_to = [("웃", "b@c.d"), "e@f.g"]
    assert m.mail_to == [("웃", "b@c.d"), (None, "e@f.g")]


def test_rfc6532_address():
    m = Message()
    m.mail_to = "anaïs@example.com"
    m.html = 'X'
    assert m.as_string()


def test_message_policy():

    if is_py34_plus:

        def gen_policy(**kw):
            import email.policy
            return email.policy.SMTP.clone(**kw)

        # Generate without policy
        m1 = emails.Message(**common_email_data())
        m1.policy = None
        # Just generate without policy
        m1.as_string()

        # Generate with policy
        m1 = emails.Message(**common_email_data())
        m1.policy = gen_policy(max_line_length=60)
        # WTF: This check fails.
        # assert max([len(l) for l in m1.as_string().split(b'\n')]) <= 60
        # TODO: another policy checks


def test_message_id():

    params = dict(html='...', mail_from='a@b.c', mail_to='d@e.f')

    # Check message-id not exists by default
    m = Message(**params)
    assert not m.as_message()['Message-ID']

    # Check message-id property setter
    m.message_id = 'ZZZ'
    assert m.as_message()['Message-ID'] == 'ZZZ'

    # Check message-id exists when argument specified
    m = Message(message_id=MessageID(), **params)
    assert m.as_message()['Message-ID']

    m = Message(message_id='XXX', **params)
    assert m.as_message()['Message-ID'] == 'XXX'


def test_several_recipients():

    # Test multiple recipients in "To" header

    params = dict(html='...', mail_from='a@b.c')

    m = Message(mail_to=['a@x.z', 'b@x.z'], cc='c@x.z', **params)
    assert m.as_message()['To'] == 'a@x.z, b@x.z'
    assert m.as_message()['cc'] == 'c@x.z'

    m = Message(mail_to=[('♡', 'a@x.z'), ('웃', 'b@x.z')], **params)
    assert m.as_message()['To'] == '=?utf-8?b?4pmh?= <a@x.z>, =?utf-8?b?7JuD?= <b@x.z>'

    # Test sending to several emails

    backend = InMemoryBackend()
    m = Message(mail_to=[('♡', 'a@x.z'), ('웃', 'b@x.z')], cc=['c@x.z', 'b@x.z'], bcc=['c@x.z', 'd@x.z'], **params)
    m.send(smtp=backend)
    for addr in ['a@x.z', 'b@x.z', 'c@x.z', 'd@x.z']:
        assert len(backend.messages[addr]) == 1


def test_transform():
    message = Message(html='''<style>h1{color:red}</style><h1>Hello world!</h1>''')
    message.transform()
    assert message.html == '<html><head><meta content="text/html; charset=utf-8" http-equiv="Content-Type"/></head>' \
                           '<body><h1 style="color:red">Hello world!</h1></body></html>'
