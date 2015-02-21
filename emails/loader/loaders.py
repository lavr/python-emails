# encoding: utf-8
import os
import os.path
import logging
import os.path
from emails.compat import to_unicode
from emails.compat import urlparse
from emails.transformer import Transformer
from emails.loader import local_store
import requests
from .helpers import guess_charset


class HTTPLoaderError(Exception):
    pass

class BaseLoader(object):

    USER_AGENT = 'python-emails/1.1'

    def __init__(self, requests_params=None,
                 css_inline=True,
                 remove_unsafe_tags=True,
                 make_links_absolute=False,
                 set_content_type_meta=True,
                 update_stylesheet=True,
                 images_inline=False,
                 **kwargs):

        self.requests_params = requests_params
        self.transformer = None
        self.css_inline = css_inline

    def fetch_url(self, url, valid_http_codes=(200, ), params=None):
        args = dict(allow_redirects=True, headers={'User-Agent': self.USER_AGENT})
        requests_params = params or self.requests_params
        if requests_params:
            args.update(requests_params)
        response = requests.get(url, **args)
        if valid_http_codes and (response.status_code not in valid_http_codes):
            raise HTTPLoaderError('Error loading url: %s. HTTP status: %s' % (url, response.http_status))
        return response

    def to_message(self):
        pass

    @property
    def html(self):
        return self.transformer.to_string()

    @property
    def text(self):
        return None

    @property
    def attachments_dict(self):
        return list(self.transformer.attachment_store.as_dict())

    @property
    def attachments(self):
        return self.transformer.attachment_store.as_dict()


def _make_base_url(url):
    # /a/b.html -> /a
    p = list(urlparse.urlparse(url))[:5]
    p[2] = os.path.split(p[2])[0]
    return urlparse.urlunsplit(p)


class URLLoader(BaseLoader):

    def __init__(self, url, **kwargs):
        self.url = url
        self._html = None
        self.kwargs = kwargs
        super(URLLoader, self).__init__(**kwargs)

    def load(self):
        # Load html page
        r = self.fetch_url(self.url)

        html = r.content
        html = to_unicode(html, charset=guess_charset(r.headers, html))
        html = html.replace('\r\n', '\n')  # Remove \r
        self._html = html

        # This is for premailer
        self.base_url = _make_base_url(self.url)

        # Transform html
        self.transformer = Transformer(html=self._html, base_url=self.base_url, **self.kwargs)
        self.transformer.transform()


class DirectoryLoader(BaseLoader):

    def __init__(self, directory, index_file=None, **kwargs):
        self.directory = directory
        self.index_file = index_file
        self.kwargs = kwargs
        super(DirectoryLoader, self).__init__(**kwargs)

    def load(self):
        store = local_store.FileSystemLoader(searchpath=self.directory)
        index_file_name = store.find_index_file(self.index_file)
        dirname, basename = os.path.split(index_file_name)
        if dirname:
            store.base_path = dirname

        # Transform html
        self.transformer = Transformer(html=store[index_file_name],
                                       local_loader=store,
                                       **self.kwargs)
        self.transformer.transform()


class StringLoader(BaseLoader):

    def __init__(self, html, **kwargs):
        self.html = html
        self.kwargs = kwargs
        super(StringLoader, self).__init__(**kwargs)

    def load(self):
        # Transform html
        self.transformer = Transformer(html=self.html, **self.kwargs)
        self.transformer.transform()


class ZipLoader(BaseLoader):

    def __init__(self, zip_file, **kwargs):
        self.zip_file = zip_file
        self.kwargs = kwargs
        super(ZipLoader, self).__init__(**kwargs)

    def load(self):
        store = local_store.ZipLoader(file=self.zip_file)
        index_file_name = store.find_index_file()
        dirname, index_file_name = os.path.split(index_file_name)
        if dirname:
            store.base_path = dirname
        logging.debug('from_zip: found index file: %s', index_file_name)
        # Transform html
        self.transformer = Transformer(html=store[index_file_name],
                                       local_loader=store,
                                       **self.kwargs)
        self.transformer.transform()

