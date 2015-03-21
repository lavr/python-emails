# encoding: utf-8
from __future__ import unicode_literals, print_function
import glob
import email

import os.path
from emails.compat import to_native
import emails.loader
from emails.loader.local_store import MsgLoader

ROOT = os.path.dirname(__file__)


def _get_message():
    m = emails.loader.from_zip(open(os.path.join(ROOT, "data/html_import/oldornament/oldornament.zip"), 'rb'))
    m.text = 'text'
    n = len(m.attachments)
    for i, a in enumerate(m.attachments):
        a.content_disposition = 'inline' if i < n/2 else 'attachment'
    m.transformer.synchronize_inline_images()
    m.transformer.save()
    #open('oldornament.eml', 'wb').write(m.as_string())
    return m


def _compare_messages(a, b):
    assert a.text == b.text
    assert a.html and a.html == b.html
    assert len(a.attachments) == len(b.attachments)
    assert sorted([att.filename for att in a.attachments]) == sorted([att.filename for att in b.attachments])
    for att in a.attachments:
        assert att.data == b.attachments.by_filename(att.filename).data


def test_rfc822_loader(**kw):
    source_message = _get_message()
    message = emails.loader.from_rfc822(source_message.as_string(), **kw)
    _compare_messages(message, source_message)
    assert len(message.attachments.by_filename('arrow.png').data) == 484


def test_msgloader():

    data = {'charset': 'utf-8',
            'subject': 'Что-то по-русски',
            'mail_from': ('Максим Иванов', 'ivanov@ya.ru'),
            'mail_to': ('Полина Сергеева', 'polina@mail.ru'),
            'html': '<h1>Привет!</h1><p>В первых строках...',
            'text': 'Привет!\nВ первых строках...',
            'headers': {'X-Mailer': 'python-emails'},
            'attachments': [{'data': 'X', 'filename': 'Event.ics'},
                            {'data': 'Y', 'filename': 'Map.png', 'content_disposition': 'inline'},],
            'message_id': 'message_id'}

    source_message = emails.Message(**data)
    loader = MsgLoader(msg=source_message.as_string())
    assert loader.html == data['html']
    assert loader.text == data['text']

    assert 'Event.ics' in loader.list_files()
    assert loader.content('Event.ics') == 'X'

    # check file search by content-id
    map_cid = "cid:%s" % source_message.attachments['Map.png'].content_id
    assert loader.content(map_cid) == 'Y'

    m2 = emails.loader.from_rfc822(msg=source_message.as_string(), parse_headers=True)
    assert m2.subject == data['subject']
    assert m2.as_string()
    # TODO: more tests


def _try_decode(s, charsets=('utf-8', 'koi8-r', 'cp1251')):
    for charset in charsets:
        try:
            return to_native(s, charset), charset
        except UnicodeDecodeError:
            pass
    return None, None


"""
def test_relaxed_header_parser():

    # Test broken address header without email
    from email.header import Header
    text = u'웃'
    assert list(_relaxed_parse_address_header(str(Header(text, 'utf-8'))))[0] == text

    # Test broken encoding
    #assert _try_decode(b'"\xc0\xed\xe3\xe5\xed\xee\xe2\xe0"', ['utf-8', 'koi8-r', 'cp1251', 'latin-1']) == ('', 'koi8')
    #assert list(_relaxed_parse_address_header(b'"\xc0\xed\xe3\xe5\xed\xee\xe2\xe0" <a@b.tld>'))[0] == ''
"""

def test_mass_msgloader():
    import encodings
    encodings.aliases.aliases['win_1251'] = 'cp1251'  # data-specific
    ROOT = os.path.dirname(__file__)
    for filename in glob.glob(os.path.join(ROOT, "data/msg/*.eml")):
        msg, charset = _try_decode(open(filename, 'rb').read())
        if msg is None:
            print("can not read filename=", filename)
            continue
        #msgloader = MsgLoader(msg=msg)
        print(filename)
        message = emails.loader.from_rfc822(msg=msg, parse_headers=True)
        if message._headers:
            print(message._headers)
        #message.as_string()
        #print(len(msgloader.attachments))

