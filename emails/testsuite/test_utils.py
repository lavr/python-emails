# encoding: utf-8
from __future__ import unicode_literals
from emails.utils import parse_name_and_email


def test_parse_name_and_email():
    assert parse_name_and_email('john@smith.me') == (None, 'john@smith.me')
    assert parse_name_and_email('"John Smith" <john@smith.me>') == \
           ('John Smith', 'john@smith.me')
    assert parse_name_and_email(['John Smith', 'john@smith.me']) == \
           ('John Smith', 'john@smith.me')