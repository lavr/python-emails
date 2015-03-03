# encoding: utf-8
import os
import os.path
from emails.loader.local_store import FileNotFound
from emails.compat import to_unicode
from emails.compat import urlparse
from emails import Message
from emails.utils import fetch_url
from emails.loader import local_store
from emails.loader.helpers import guess_charset


class LoadError(Exception):
    pass


class IndexFileNotFound(LoadError):
    pass


class InvalidHtmlFile(LoadError):
    pass


def from_url(url, message_params=None, requests_params=None, **kwargs):

    def _make_base_url(url):
        # /a/b.html -> /a
        p = list(urlparse.urlparse(url))[:5]
        p[2] = os.path.split(p[2])[0]
        return urlparse.urlunsplit(p)

    # Load html page
    r = fetch_url(url, requests_args=requests_params)
    html = r.content
    html = to_unicode(html, charset=guess_charset(r.headers, html))
    html = html.replace('\r\n', '\n')  # Remove \r

    message_params = message_params or {}
    message = Message(html=html, **message_params)
    message.create_transformer(requests_params=requests_params,
                               base_url=_make_base_url(url))
    message.transformer.load_and_transform(**kwargs)
    message.transformer.save()
    return message

load_url = from_url


def from_directory(directory, index_file=None, message_params=None, **kwargs):

    store = local_store.FileSystemLoader(searchpath=directory)

    try:
        index_file_name = store.find_index_file(index_file)
    except FileNotFound:
        # reraise another exception
        raise IndexFileNotFound('html file not found')

    dirname, _ = os.path.split(index_file_name)
    if dirname:
        store.base_path = dirname

    message_params = message_params or {}
    message = Message(html=store.content(index_file_name, is_html=True, guess_charset=True), **message_params)
    message.create_transformer(local_loader=store, requests_params=kwargs.pop('requests_params', None))
    if message.transformer.tree is None:
        raise InvalidHtmlFile("Error parsing file '%s'" % index_file_name)
    message.transformer.load_and_transform(**kwargs)
    message.transformer.save()
    return message


def from_file(filename, **kwargs):
    return from_directory(directory=os.path.dirname(filename), index_file=os.path.basename(filename), **kwargs)


def from_zip(zip_file, message_params=None, **kwargs):
    store = local_store.ZipLoader(file=zip_file)

    try:
        origin_index_file_name = store.find_index_file()
    except FileNotFound:
        # reraise another exception
        raise IndexFileNotFound('html file not found')

    dirname, index_file_name = os.path.split(origin_index_file_name)
    if dirname:
        store.base_path = dirname

    message_params = message_params or {}
    message = Message(html=store.content(index_file_name, is_html=True, guess_charset=True), **message_params)
    message.create_transformer(local_loader=store, requests_params=kwargs.pop('requests_params', None))
    if message.transformer.tree is None:
        raise InvalidHtmlFile("Error parsing file '%s'" % origin_index_file_name)
    message.transformer.load_and_transform(**kwargs)
    message.transformer.save()
    return message


def from_html(html, base_url=None, message_params=None, **kwargs):
    message_params = message_params or {}
    message = Message(html=html, **message_params)
    message.create_transformer(requests_params=kwargs.get('requests_params'), base_url=base_url)
    message.transformer.load_and_transform(**kwargs)
    message.transformer.save()
    return message

from_string = from_html


def from_rfc822(msg, message_params=None, **kw):

    store = local_store.MsgLoader(msg=msg)
    text = store['__index.txt']
    html = store['__index.html']

    message_params = message_params or {}
    message = Message(html=html, text=text, **message_params)
    if html:
        message.create_transformer(local_loader=store, **kw)
        message.transformer.load_and_transform()
        message.transformer.save()
    else:
        # TODO: add attachments for text-only message
        pass

    return message