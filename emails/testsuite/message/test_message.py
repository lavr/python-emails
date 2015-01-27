# coding: utf-8
from __future__ import unicode_literals

import emails
from emails.compat import StringIO
from emails.template import JinjaTemplate
from emails.compat import NativeStringIO, to_bytes

from .helpers import TRAVIS_CI, HAS_INTERNET_CONNECTION, _email_data, common_email_data


def test_message_build():
    kwargs = common_email_data()
    m = emails.Message(**kwargs)
    assert m.as_string()




def test_after_build():

    AFTER_BUILD_HEADER = 'X-After-Build'

    def my_after_build(original_message, built_message):
        built_message[AFTER_BUILD_HEADER] = '1'

    kwargs = common_email_data()
    m = emails.Message(**kwargs)
    m.after_build = my_after_build

    assert AFTER_BUILD_HEADER in m.as_string()


# TODO: more tests here
