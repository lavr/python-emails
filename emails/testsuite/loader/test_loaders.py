# encoding: utf-8
from __future__ import unicode_literals
import glob
import os.path
import email
from requests import ConnectionError
import emails
import emails.loader
import emails.transformer
from emails.loader.local_store import MsgLoader

ROOT = os.path.dirname(__file__)

BASE_URL = 'http://lavr.github.io/python-emails/tests/campaignmonitor-samples/oldornament'


def _get_messages(**kw):
    # All loaders loads same data
    yield emails.loader.from_url(BASE_URL + '/index.html', **kw)
    yield emails.loader.from_file(os.path.join(ROOT, "data/html_import/oldornament/index.html"), **kw)
    yield emails.loader.from_zip(open(os.path.join(ROOT, "data/html_import/oldornament.zip"), 'rb'), **kw)


def normalize_html(s):
    def _remove_base_url(src, **kw):
        if src.startswith(BASE_URL):
            return src[len(BASE_URL)+1:]
        else:
            return src

    # Use Transformer not for test, just to walk tree
    t = emails.transformer.Transformer(html=s)
    t.apply_to_links(_remove_base_url)
    t.apply_to_images(_remove_base_url)
    return t.to_string()


def all_equals(seq):
    iseq = iter(seq)
    first = next(iseq)
    return all(x == first for x in iseq)


def test_loaders():

    messages = list(_get_messages(requests_params={'timeout': 10}))

    # Check loaded images
    for m in messages:
        assert len(m.attachments.keys()) == 13

    valid_filenames = ['arrow.png', 'banner-bottom.png', 'banner-middle.gif', 'banner-top.gif', 'bg-all.jpg',
                       'bg-content.jpg', 'bg-main.jpg', 'divider.jpg', 'flourish.png', 'img01.jpg', 'img02.jpg',
                       'img03.jpg', 'spacer.gif']
    assert sorted([a.filename for a in messages[0].attachments]) == sorted(valid_filenames)
    assert len(messages[0].attachments.by_filename('arrow.png').data) == 484

    # Simple html content check
    htmls = [normalize_html(m.html) for m in messages]
    assert 'Lorem Ipsum Dolor Sit Amet' in htmls[0]
    assert all_equals(htmls)


def _test_external_urls():

    # Load some real sites with complicated html and css.
    # Test loader don't throw any exception.

    for url in [
                'https://github.com/lavr/python-emails',
                'http://yandex.com',
                'http://www.smashingmagazine.com/'
                ]:
        try:
            emails.loader.from_url(url)
        except ConnectionError:
            # Nevermind if external site does not respond
            pass


def test_msgloader():

    data = {'charset': 'utf-8',
            'subject': 'Что-то по-русски',
            'mail_from': ('Максим Иванов', 'ivanov@ya.ru'),
            'mail_to': ('Полина Сергеева', 'polina@mail.ru'),
            'html': '<h1>Привет!</h1><p>В первых строках...',
            'text': 'Привет!\nВ первых строках...',
            'headers': {'X-Mailer': 'python-emails'},
            'attachments': [{'data': 'aaa', 'filename': 'Event.ics'},],
            'message_id': 'message_id'}

    msg = emails.Message(**data).as_string()
    loader = MsgLoader(msg=msg)
    loader._parse_msg()
    assert 'Event.ics' in loader.list_files()
    assert loader['__index.html'] == data['html']
    assert loader['__index.txt'] == data['text']


def _test_mass_msgloader():
    ROOT = os.path.dirname(__file__)
    for filename in glob.glob(os.path.join(ROOT, "data/msg/*.eml")):
        msg = email.message_from_string(open(filename).read())
        msgloader = MsgLoader(msg=msg)
        msgloader._parse_msg()