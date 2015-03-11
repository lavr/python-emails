# encoding: utf-8
import os
import os.path

from .local_store import (FileSystemLoader, ZipLoader, MsgLoader, FileNotFound)
from .helpers import guess_charset
from ..compat import to_unicode
from ..compat import urlparse
from ..message import Message
from ..utils import fetch_url


class LoadError(Exception):
    pass


class IndexFileNotFound(LoadError):
    pass


class InvalidHtmlFile(LoadError):
    pass


def from_html(html, text=None, base_url=None, message_params=None, local_loader=None,
              template_cls=None, message_cls=None, source_filename=None, requests_params=None,
              **kwargs):

    if template_cls:
        html = template_cls(html)

    message_params = message_params or {}

    text = text or message_params.pop('text', None)
    if template_cls and text:
        text = template_cls(text)

    message = (message_cls or Message)(html=html, text=text, **message_params)
    message.create_transformer(requests_params=requests_params,
                               base_url=base_url,
                               local_loader=local_loader)
    if message.transformer.tree is None:
        raise InvalidHtmlFile("Error parsing '%s'" % source_filename)
    message.transformer.load_and_transform(**kwargs)
    message.transformer.save()
    return message


from_string = from_html


def from_url(url, requests_params=None, **kwargs):

    def _extract_base_url(url):
        # /a/b.html -> /a
        p = list(urlparse.urlparse(url))[:5]
        p[2] = os.path.split(p[2])[0]
        return urlparse.urlunsplit(p)

    # Load html page
    r = fetch_url(url, requests_args=requests_params)
    html = r.content
    html = to_unicode(html, charset=guess_charset(r.headers, html))
    html = html.replace('\r\n', '\n')  # Remove \r

    return from_html(html,
                     base_url=_extract_base_url(url),
                     source_filename=url,
                     requests_params=requests_params,
                     **kwargs)


load_url = from_url


def _from_filebased_source(store, html_filename=None, skip_text=True, text_filename=None, message_params=None, **kwargs):

    try:
        html_filename = store.find_index_html(html_filename)
    except FileNotFound:
        raise IndexFileNotFound('html file not found')

    dirname, html_filename = os.path.split(html_filename)
    if dirname:
        store.base_path = dirname

    html = store.content(html_filename, is_html=True, guess_charset=True)

    text = None
    if not skip_text:
        text_filename = store.find_index_text(text_filename)
        text = text_filename and store.content(text_filename) or None

    return from_html(html=html,
                     text=text,
                     local_loader=store,
                     source_filename=html_filename,
                     message_params=message_params,
                     **kwargs)


def from_directory(directory, loader_cls=None, **kwargs):
    loader_cls = loader_cls or FileSystemLoader
    return _from_filebased_source(store=loader_cls(searchpath=directory), **kwargs)


def from_file(filename, **kwargs):
    return from_directory(directory=os.path.dirname(filename), html_filename=os.path.basename(filename), **kwargs)


def from_zip(zip_file, loader_cls=None, **kwargs):
    loader_cls = loader_cls or ZipLoader
    return _from_filebased_source(store=loader_cls(file=zip_file), **kwargs)


def from_rfc822(msg, message_params=None):
    # Warning: from_rfc822 is for demo purposes only
    loader = MsgLoader(msg=msg)
    message_params = message_params or {}
    message = Message(html=loader.html, text=loader.text, **message_params)
    for att in loader.attachments:
        message.attachments.add(att)
    return message