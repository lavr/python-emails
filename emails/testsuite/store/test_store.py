# encoding: utf-8
from __future__ import unicode_literals
import pytest
import emails
import emails.store
from emails.store.file import fix_content_type


def test_fix_content_type():
    assert fix_content_type('x') == 'x'
    assert fix_content_type('') == 'image/unknown'


def test_lazy_http():
    IMG_URL = 'http://lavr.github.io/python-emails/tests/python-logo.gif'
    f = emails.store.LazyHTTPFile(uri=IMG_URL)
    assert f.filename == 'python-logo.gif'
    assert f.content_disposition == 'attachment'
    assert len(f.data) == 2549


def test_attachment_headers():
    f = emails.store.BaseFile(data='x', filename='1.txt', headers={'X-Header': 'X'})
    part = f.mime.as_string()
    assert 'X-Header: X' in part


def test_get_mime_type_by_extension():
    f = emails.store.BaseFile(data='x', filename='logo.jpg')
    assert f.mime_type == 'image/jpeg'


def test_get_mime_type_from_data_jpeg():
    f = emails.store.BaseFile(
        data=b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01',
        filename='thumb',
    )
    assert f.mime_type == 'image/jpeg'


def test_get_mime_type_from_data_png():
    f = emails.store.BaseFile(
        data=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00d',
        filename='thumb',
    )
    assert f.mime_type == 'image/png'


def test_get_mime_type_from_data_gif():
    f = emails.store.BaseFile(
        data=b'GIF89a\xd3\x00G\x00\xf7\x00\x00\xff\xff',
        filename='thumb',
    )
    assert f.mime_type == 'image/gif'


def test_store_commons():
    FILES = [{'data': 'aaa', 'filename': 'aaa.txt'}, {'data': 'bbb', 'filename': 'bbb.txt'}, ]
    store = emails.store.MemoryFileStore()
    [store.add(_) for _ in FILES]
    for i, stored_file in enumerate(store):
        orig_file = FILES[i]
        for (k, v) in orig_file.items():
            assert v == getattr(stored_file, k)


def test_store_unique_name():
    store = emails.store.MemoryFileStore()
    f1 = store.add({'uri': '/a/c.gif'})
    assert f1.filename == 'c.gif'
    f2 = store.add({'uri': '/a/b/c.gif'})
    assert f2.filename == 'c-2.gif'
    assert f1.content_id != f2.content_id
    f3 = store.add({'uri': '/a/c/c.gif'})
    assert f3.filename == 'c-3.gif'
    assert f1.content_id != f3.content_id
    assert f2.content_id != f3.content_id


def test_store_commons2():
    store = emails.store.MemoryFileStore()
    f1 = store.add({'uri': '/a/c.gif'})
    assert f1.filename
    assert f1.content_id
    assert f1 in store and f1.uri in store  # tests __contains__
    assert len(store) == 1  # tests __len__
    assert len(list(store.as_dict())) == 1
    with pytest.raises(ValueError):
        store.add("X")
    store.remove(f1)
    assert f1 not in store
    assert len(store) == 0
