# encoding: utf-8
from __future__ import unicode_literals
import pytest
from emails.utils import (parse_name_and_email,
    encode_header, decode_header, sanitize_address, fetch_url)
from emails.exc import HTTPLoaderError

def test_parse_name_and_email():
    assert parse_name_and_email('john@smith.me') == (None, 'john@smith.me')
    assert parse_name_and_email('"John Smith" <john@smith.me>') == \
           ('John Smith', 'john@smith.me')
    assert parse_name_and_email(['John Smith', 'john@smith.me']) == \
           ('John Smith', 'john@smith.me')
    with pytest.raises(ValueError):
        parse_name_and_email(1)


def test_header_encode():
    v = 'Мама мыла раму. ' * 30
    assert decode_header(encode_header(v)).strip() == v.strip()
    assert encode_header(1) == 1


def test_sanitize_address():
    assert sanitize_address('a <b>') == 'a <b>'
    assert sanitize_address('a@b.d') == 'a@b.d'
    assert sanitize_address('x y <a@b.d>') == 'x y <a@b.d>'
    assert sanitize_address('♤ <a@b.d>') == '=?utf-8?b?4pmk?= <a@b.d>'
    assert sanitize_address('a@♤.d') == 'a@xn--f6h.d'


def test_fetch_url():
    fetch_url('http://google.com')
    with pytest.raises(HTTPLoaderError):
        fetch_url('http://google.com/nonexistent-no-page')

