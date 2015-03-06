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

BASE_URL = 'http://lavr.github.io/python-emails/tests/'

OLDORNAMENT_URLS = dict(from_url='campaignmonitor-samples/oldornament/index.html',
                        from_file='data/html_import/oldornament/oldornament/index.html',
                        from_zip='data/html_import/oldornament/oldornament.zip')


def load_messages(from_url=None, from_file=None, from_zip=None, from_directory=None, **kw):
    # Ususally all loaders loads same data
    if from_url:
        print("emails.loader.from_url", BASE_URL + from_url, kw)
        yield emails.loader.from_url(BASE_URL + from_url, **kw)
    if from_file:
        print("emails.loader.from_file", os.path.join(ROOT, from_file), kw)
        yield emails.loader.from_file(os.path.join(ROOT, from_file), **kw)
    if from_directory:
        print("emails.loader.from_directory", os.path.join(ROOT, from_directory), kw)
        yield emails.loader.from_directory(os.path.join(ROOT, from_directory), **kw)
    if from_zip:
        print("emails.loader.from_zip", os.path.join(ROOT, from_zip), kw)
        yield emails.loader.from_zip(open(os.path.join(ROOT, from_zip), 'rb'), **kw)



def test_loaders():

    def _all_equals(seq):
        iseq = iter(seq)
        first = next(iseq)
        return all(x == first for x in iseq)

    _base_url = os.path.dirname(BASE_URL + OLDORNAMENT_URLS['from_url']) + '/'
    def _remove_base_url(src, **kw):
        if src.startswith(_base_url):
            return src[len(_base_url):]
        else:
            return src

    message_params = {'subject': 'X', 'mail_to': 'a@b.net'}

    htmls = []
    rfc_strings = []

    for message in load_messages(message_params=message_params, **OLDORNAMENT_URLS):
        # Check loaded images
        assert len(message.attachments.keys()) == 13

        valid_filenames = ['arrow.png', 'banner-bottom.png', 'banner-middle.gif', 'banner-top.gif', 'bg-all.jpg',
                           'bg-content.jpg', 'bg-main.jpg', 'divider.jpg', 'flourish.png', 'img01.jpg', 'img02.jpg',
                           'img03.jpg', 'spacer.gif']
        assert sorted([a.filename for a in message.attachments]) == sorted(valid_filenames)
        print(type(message.attachments))
        assert len(message.attachments.by_filename('arrow.png').data) == 484

        # Simple html content check
        assert 'Lorem Ipsum Dolor Sit Amet' in message.html

        # Simple message build check
        message.as_string()

        # Normalize html and save for later check
        message.transformer.apply_to_links(_remove_base_url)
        message.transformer.apply_to_images(_remove_base_url)
        message.transformer.save()
        htmls.append(message.html)

    assert _all_equals(htmls)


def test_noindex_loaders():

    with pytest.raises(emails.loader.IndexFileNotFound):
        emails.loader.from_directory(os.path.join(ROOT, 'data/html_import/no-index/no-index/'))

    with pytest.raises(emails.loader.IndexFileNotFound):
        emails.loader.from_zip(open(os.path.join(ROOT, 'data/html_import/no-index/no-index.zip'), 'rb'))


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
        args = {}
        args.update(tp)
        args.update(OLDORNAMENT_URLS)
        for m in load_messages(requests_params={'timeout': 10},
                               message_params=message_params,
                               **args):
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
    loader._parse_msg()
    assert 'Event.ics' in loader.list_files()
    assert loader['__index.html'] == data['html']
    assert loader['__index.txt'] == data['text']

    assert emails.loader.from_rfc822(msg=msg).as_string()
    # TODO: more tests


def _test_mass_msgloader():
    ROOT = os.path.dirname(__file__)
    for filename in glob.glob(os.path.join(ROOT, "data/msg/*.eml")):
        msg = email.message_from_string(open(filename).read())
        msgloader = MsgLoader(msg=msg)
        msgloader._parse_msg()


def _get_loaders():
    # All loaders loads same data
    yield FileSystemLoader(os.path.join(ROOT, "data/html_import/./oldornament/oldornament"))
    yield ZipLoader(open(os.path.join(ROOT, "data/html_import/oldornament/oldornament.zip"), 'rb'))


def test_local_store1():
    for loader in _get_loaders():
        print(loader)
        assert isinstance(loader.content('index.html'), text_type)
        assert isinstance(loader['index.html'], bytes)
        assert '<table' in loader.content('index.html')
        with pytest.raises(FileNotFound):
            loader.get_file('-nonexistent-file')
        with pytest.raises(FileNotFound):
            loader.find_index_file('-nonexistent-file')
        files_list = list(loader.list_files())
        assert 'images/arrow.png' in files_list
        assert len(files_list) in [15, 16]
        # TODO: remove directories from zip loader list_files results


def test_split_template_path():

    with pytest.raises(FileNotFound):
        split_template_path('../a.git')


def test_base_loader():

    # Prepare simple BaseLoader
    class TestBaseLoader(BaseLoader):
        _files = []
        def list_files(self):
            return self._files
        def get_file(self, name):
            return ('xxx', name) if name in self.list_files() else (None, name)

    l = TestBaseLoader()
    l._files = ['__MACOSX/.index.html', 'a.html', 'b.html']
    # Check index file search
    assert l.find_index_file() == 'a.html'

    # Check .content works
    assert l.content('a.html') == 'xxx'

    # Raises exception when no html file
    l._files = ['a.gif', '__MACOSX/.index.html']
    with pytest.raises(FileNotFound):
        print(l.find_index_file())