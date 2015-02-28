# encoding: utf-8
from __future__ import unicode_literals, print_function
import glob
import os.path
import email
import pytest
from requests import ConnectionError
import emails
import emails.loader
import emails.transformer
from emails.loader.local_store import (MsgLoader, FileSystemLoader, FileNotFound, ZipLoader,
                                       split_template_path, BaseLoader)
from emails.compat import text_type
from emails.loader.helpers import guess_charset

ROOT = os.path.dirname(__file__)

BASE_URL = 'http://lavr.github.io/python-emails/tests/campaignmonitor-samples/oldornament'


def _get_messages(**kw):
    # All loaders loads same data
    yield emails.loader.from_url(BASE_URL + '/index.html', **kw)
    yield emails.loader.from_file(os.path.join(ROOT, "data/html_import/oldornament/index.html"), **kw)
    yield emails.loader.from_zip(open(os.path.join(ROOT, "data/html_import/oldornament.zip"), 'rb'), **kw)
    #msg = emails.loader.from_zip(open(os.path.join(ROOT, "data/html_import/oldornament.zip"), 'rb'), **kw)
    #print("emails.loader.from_rfc822")
    #yield emails.loader.from_rfc822(msg.as_string(), **kw)


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

    message_params = {'subject': 'X', 'mail_to': 'a@b.net'}

    htmls = []
    rfc_strings = []

    for message in _get_messages(message_params=message_params):
        # Check loaded images
        assert len(message.attachments.keys()) == 13

        valid_filenames = ['arrow.png', 'banner-bottom.png', 'banner-middle.gif', 'banner-top.gif', 'bg-all.jpg',
                           'bg-content.jpg', 'bg-main.jpg', 'divider.jpg', 'flourish.png', 'img01.jpg', 'img02.jpg',
                           'img03.jpg', 'spacer.gif']
        assert sorted([a.filename for a in message.attachments]) == sorted(valid_filenames)
        print(type(message.attachments))
        assert len(message.attachments.by_filename('arrow.png').data) == 484

        # Simple html content check
        html = normalize_html(message.html)
        assert 'Lorem Ipsum Dolor Sit Amet' in html
        htmls.append(html)

        # Simple string check
        rfc_string = message.as_string()
        rfc_strings.append(rfc_string)

    assert all_equals(htmls)


def test_loaders_with_params():

    transform_params = [ dict(css_inline=True,
                            remove_unsafe_tags=True,
                            make_links_absolute=True,
                            set_content_type_meta=True,
                            update_stylesheet=True,
                            load_images=True,
                            images_inline=True),

                         dict(css_inline=False,
                              remove_unsafe_tags=False,
                              make_links_absolute=False,
                              set_content_type_meta=False,
                              update_stylesheet=False,
                              load_images=False,
                              images_inline=False)
                         ]

    message_params = {'subject': 'X', 'mail_to': 'a@b.net'}

    for tp in transform_params:
        for m in _get_messages(requests_params={'timeout': 10},
                               message_params=message_params,
                               **tp):
            assert m.subject == message_params['subject']
            assert m.mail_to[0][1] == message_params['mail_to']
            for a in m.attachments:
                assert a.is_inline is True


def test_external_urls():

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
    assert 'Event.ics' in loader.list_files()
    assert loader['__index.html'] == data['html']
    assert loader['__index.txt'] == data['text']



def _test_mass_msgloader():
    ROOT = os.path.dirname(__file__)
    for filename in glob.glob(os.path.join(ROOT, "data/msg/*.eml")):
        msg = email.message_from_string(open(filename).read())
        msgloader = MsgLoader(msg=msg)
        msgloader._parse_msg()


def test_local_file_store1():

    for loader in [FileSystemLoader(os.path.join(ROOT, "data/html_import/oldornament/")),
                   ZipLoader(open(os.path.join(ROOT, "data/html_import/oldornament.zip"), 'rb'))]:
        print(loader)
        index_html = 'index.html'
        assert isinstance(loader[index_html], bytes)
        assert isinstance(loader.content(index_html), text_type)
        assert '<table' in loader.content(index_html)
        with pytest.raises(FileNotFound):
            loader.get_file('-nonexistent-file')
        with pytest.raises(FileNotFound):
            loader.find_index_file('-nonexistent-file')
        files_list = list(loader.list_files())
        assert 'images/arrow.png' in files_list
        assert len(files_list) in [15, 16]
        # TODO: remove directories from zip loader list_files results


def test_directory_loader():

    with pytest.raises(FileNotFound):
        split_template_path('../a.git')


def test_base_loader():

    l = BaseLoader()
    l.list_files = lambda **kw: ['a.html', 'b.html']
    l.get_file = lambda obj, name: ('xxx', name) if name in obj.list_files() else (None, name)

    assert l.find_index_file() == l.list_files()[0]

    # is no html file
    l.list_files = lambda **kw: ['a.gif', ]
    with pytest.raises(FileNotFound):
        print(l.find_index_file())


def test_local_msgloader():

    def _get_rfc_message():
        m = emails.loader.from_zip(open(os.path.join(ROOT, "data/html_import/oldornament.zip"), 'rb'))
        n = len(m.attachments)
        for i, a in enumerate(m.attachments):
            a.content_disposition = 'inline' if i < n/2 else 'attachment'
        m.transformer.synchronize_inline_images()
        m.transformer.save()
        #open('oldornament.eml', 'wb').write(m.as_string())
        return m.as_string()


    for loader in [MsgLoader(msg=_get_rfc_message()), ]:
        loader.parse()
        print(loader)
        index_html = '__index.html'
        assert isinstance(loader.content(index_html), text_type)
        assert '<table' in loader.content(index_html)
        with pytest.raises(FileNotFound):
            loader.get_file('-nonexistent-file')
        with pytest.raises(FileNotFound):
            loader.find_index_file('-nonexistent-file')
        files_list = list(loader.list_files())
        print("files_list=", files_list)
        assert len(files_list) == 14
        assert 'arrow.png' in files_list
        assert len(loader['arrow.png']) == 484
