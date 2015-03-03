# coding: utf-8
from __future__ import unicode_literals, print_function

import emails
from emails.compat import to_unicode
from .helpers import common_email_data


def test_message_build():
    kwargs = common_email_data()
    m = emails.Message(**kwargs)
    assert m.as_string()
    open('_common_email_data.eml', 'wb').write(m.as_string())


def test_property_works():
    m = emails.Message(subject='A')
    assert m._subject == 'A'
    m.subject = 'C'
    assert m._subject == 'C'


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


# TODO: more tests here
