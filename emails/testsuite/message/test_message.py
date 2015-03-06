# coding: utf-8
from __future__ import unicode_literals, print_function
import datetime
from dateutil.parser import parse as dateutil_parse
import pytest
import emails
import emails.exc
from emails.compat import to_unicode, StringIO, is_py2, is_py3
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
    assert dateutil_parse(m.message_date).replace(tzinfo=None) >= datetime.datetime.now() - datetime.timedelta(seconds=3)

    # check date as constant
    m.message_date = '2015-01-01'
    assert m.message_date.startswith('Thu, 01 Jan 2015 00:00:00')

    # check date as func
    m.message_date = lambda **kw: 'D'
    assert m.message_date == 'D'


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


def test_sanitize_header():
    for header, value in (
            ('subject', 'test\n'),
            ('headers', {'X-Header': 'test\r'}),
            ):
        with pytest.raises(emails.exc.BadHeaderError):
            print('header {0}'.format(header))
            emails.Message(html='...', **{header: value}).as_message()

# TODO: more tests here
