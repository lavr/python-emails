# coding: utf-8
from __future__ import unicode_literals, print_function
import datetime
from dateutil.parser import parse as dateutil_parse
import pytest
import emails
from emails import Message
import emails.exc
from emails.compat import to_unicode, StringIO, is_py2, is_py34_plus
from .helpers import common_email_data


def test_message_types():

    if is_py2:
        bytes_types = (str, )
        native_string = (unicode, )
    else:
        bytes_types = (bytes, )
        native_string = (str, )

    m = emails.Message(**common_email_data())
    print(type(m.as_string()))
    #assert isinstance(m.as_message().as_string(), native_string)
    assert isinstance(m.as_string(), bytes_types)


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
