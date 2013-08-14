# encoding: utf-8

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import uuid

from os.path import splitext, basename

import requests
from mimetypes import guess_type
from email.mime.base import MIMEBase
from email.encoders import encode_base64

# class FileNotFound(Exception):
#    pass


def fix_content_type(content_type, t='image'):
    if (not content_type):
        return "%s/unknown" % t
    else:
        return content_type


class BaseFile(object):

    """
    Store base "attachment-file" information.
    """

    def __init__(self, **kwargs):
        """
        uri and filename are connected properties.
        if no filename set, filename extracted from uri.
        if no uri, but filename set, then uri==filename
        """
        self.uri = kwargs.get('uri', None)
        self.absolute_url = kwargs.get('absolute_url', None) or self.uri
        self.filename = kwargs.get('filename', None)
        self.data = kwargs.get('data', None)
        self._mime_type = kwargs.get('mime_type', None)
        self._headers = kwargs.get('headers', None)
        self._content_disposition = kwargs.get('content_disposition', None)
        self.subtype = kwargs.get('subtype', None)
        self.id = id

    def as_dict(self, fields=None):
        fields = fields or ( 'uri', 'absolute_url', 'filename', 'data',
                            'mime_type', 'content_disposition', 'subtype')
        return dict([(k, getattr(self, k)) for k in fields])

    def get_data(self):
        _data = getattr(self, '_data', None)
        if isinstance(_data, basestring):
            return _data
        elif hasattr(_data, 'read'):
            return _data.read()
        else:
            return _data

    def set_data(self, value):
        self._data = value

    data = property(get_data, set_data)

    def get_uri(self):
        _uri = getattr(self, '_uri', None)
        if (_uri is None):
            _filename = getattr(self, '_filename', None)
            if _filename:
                _uri = self._uri = _filename
        return _uri

    def set_uri(self, value):
        self._uri = value

    uri = property(get_uri, set_uri)

    def get_filename(self):
        _filename = getattr(self, '_filename', None)
        if (_filename is None):
            _uri = getattr(self, '_uri', None)
            if _uri:
                parsed_path = urlparse(_uri)
                _filename = basename(parsed_path.path)
                if not _filename:
                    _filename = str(uuid.uuid4())
                self._filename = _filename
        return _filename

    def set_filename(self, value):
        self._filename = value

    filename = property(get_filename, set_filename)

    def get_mime_type(self):
        _ = getattr(self, '_mime_type', None)
        if (_ is None):
            filename = self.filename
            _ = self._mime_type = guess_type(filename)[0]
            # print __name__, "get_mime_type calculated=", _
        return _

    mime_type = property(get_mime_type)

    def get_content_disposition(self):
        return getattr(self, '_content_disposition', None)

    def set_content_disposition(self, value):
        self._content_disposition = value

    content_disposition = property(get_content_disposition, set_content_disposition)

    @property
    def mime(self):
        if self.content_disposition is None:
            return None
        _mime = getattr(self, '_cached_mime', None)
        if _mime is None:
            self._cached_mime = _mime = MIMEBase(*self.mime_type.split('/', 1))
            _mime.set_payload(self.data)
            encode_base64(_mime)
            _mime.add_header('Content-Disposition',
                             self.content_disposition,
                             filename=self.filename)
            if self.content_disposition == 'inline':
                _mime.add_header('Content-ID', '<%s>' % self.filename)
        return _mime

    def reset_mime(self):
        self._mime = None

    def fetch(self):
        pass


class LazyHTTPFile(BaseFile):

    def __init__(self, fetch_params=None, **kwargs):
        BaseFile.__init__(self, **kwargs)
        self.fetch_params = dict(allow_redirects=True, verify=False)
        if fetch_params:
            self.fetch_params.update(fetch_params)
        self._fetched = False

    def fetch(self):
        if (not self._fetched) and self.uri:
            r = requests.get(self.absolute_url or self.uri, **self.fetch_params)
            if r.status_code == 200:
                self._data = r.content
                self._headers = r.headers
                self._mime_type = fix_content_type(r.headers.get('content-type'), t='unknown')
                self._fetched = True

    def get_data(self):
        self.fetch()
        return self._data or ''

    def set_data(self, v):
        self._data = v

    data = property(get_data, set_data)

    @property
    def mime_type(self):
        self.fetch()
        return self._mime_type

    @property
    def headers(self):
        self.fetch()
        return self._headers
